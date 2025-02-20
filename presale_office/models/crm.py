# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api , _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from lxml import etree
from datetime import datetime as dt
import logging


_logger = logging.getLogger(__name__)
class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "tier.validation"]
    _state_from = ["draft"]
    _state_to = ["authorized"]

    _tier_validation_manual_config = False
    _tier_validation_state_field_is_computed = True

    
    presale_ids = fields.One2many('presale.order','lead_id',string="Presale project")
    requiere_preventa = fields.Boolean(string="Requiere preventa?", tracking=True,default=True)
    qty_projects_created = fields.Integer(string="Projects", compute="count_project_lead")
    qty_presale_created = fields.Integer(string="Presale Q.", compute="count_presale_lead")
    project_ids = fields.One2many('project.project','lead_id', string="Projects", track_visibility='onchange')
    state = fields.Selection([('draft', 'Borrador'),('authorized','Autorizado')],string="State",compute='_compute_state',store=True)
  
    def aprobar_prospecto(self):
        for record in self:
            record.generate_presale_project()
            stage_prospecto = self.env['crm.stage'].search([('name','=','Prospecto')])
            record.write({
                'stage_id':stage_prospecto.id
            })
    def write(self, vals):
        # Validar si el campo 'state' está en los valores y requiere validación
        for record in self:
            # Verificar si need_validation es True y validation_status no es 'validated'
            if record.need_validation and record.validation_status != 'validated':
                raise ValidationError(
                    _("La acción no se puede completar porque el registro requiere validación y no ha sido validado.")
                )
                # Detener el flujo con un return vacío
                return

        # Si pasa la validación, ejecutar la escritura
        res = super(CrmLead, self).write(vals)

        # Lógica adicional para actualizar presale.order
        get_presale_order = self.env['presale.order'].search([('lead_id', '=', self.id)])
        if get_presale_order:
            for gpo in get_presale_order:
                if not gpo or not gpo.name:
                    continue
                if "-V" in gpo.name:
                    old_name, old_substring = gpo.name.split('-V', maxsplit=1)
                    new_name = f"{vals.get('name')}-V{old_substring}"
                else:
                    new_name = vals.get('name')
                if new_name:
                    gpo.write({'name': new_name})

        return res

    @api.depends('stage_id')
    def _compute_state(self):
        for record in self:
            if record.stage_id.name in ('Prospecto','Oportunidad'):
                record.state = 'draft'
            else:
                record.state = 'authorized'

    def generate_presale_project(self):
        for rec in self:
            if not rec.name:
                raise ValidationError(_("Para crear o actualizar el nombre de la Cotizacion de Preventas,"
                                            "es necesario que rellene el campo 'Nombre'!"))
            else:
                presale_quote = self.env['presale.order']
                presale_quotes = presale_quote.search([('lead_id', '=', rec.id)])

                count_presale = len(presale_quotes)
                presale_data = {
                    'name': " -V.".join([str(rec.name), str(count_presale + 1)]),
                    'team_id': rec.team_id.id,
                    'partner_id': rec.partner_id.id,
                    'commercials_ids': [(6, 0, [rec.user_id.id])],
                    'lead_id': rec.id
                }
                presale_quote.create(presale_data)



    def generate_project_task(self):
        for rec in self:
            if rec.name != False:
                project = self.env['project.project']
                search_project = project.search_count([('lead_id','=',rec.id)])
                print(f"[PRO:]{search_project}")
                if search_project == 0:
                    comp = "TECH"
                    year = str(dt.now().year)
                    client = rec.partner_id.name

                    project_data = {
                        "name": rec.name,
                        "lead_id": rec.id
                    }
                    project.create(project_data)
                else:
                    raise ValidationError(_("Usted ya ha creado un proyecto previamente, no se pueden tener más de un proyecto por Lead!"))
            else:
                raise ValidationError(_("Para crear o actualizar el nombre del Proyecto asociado al Lead,"
                                        "es necesario que rellene el campo 'Nombre'!"))


    def count_presale_lead(self):
        for rec in self:
            count_presale_lead = self.env['presale.order'].search_count([('lead_id', '=', rec.id)])
            rec.qty_presale_created = count_presale_lead


    def get_presale_lead(self):
        if self.qty_presale_created > 0:
            return{
                'type':'ir.actions.act_window',
                'name': 'Cotizaciones de Preventa',
                'res_model':'presale.order',
                'domain': [('lead_id','=',self.id)],
                'view_mode': 'tree,form',
                'target': 'current'
            }
        else:
            raise ValidationError(_("Aún no posee una lista de Cotizaciones de Preventas relacionadas al Lead... "
                                    "Porfavor genere una antes de proceder con la acción!"))


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    presale_currency_id = fields.Many2one('res.currency',string="Related currency")


class ProjectProject(models.Model):
    _inherit = 'project.project'

    lead_id = fields.Many2one('crm.lead',strign="Lead")
