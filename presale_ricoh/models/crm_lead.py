# -*- coding: utf-8 -*-
import logging
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class CrmStage(models.Model):
    _inherit = 'crm.stage'

    genera_cotizador      = fields.Boolean(string="Genera Cotizador?")
    is_etapa_contacto     = fields.Boolean(string="Es etapa Contacto")
    is_etapa_relevamiento = fields.Boolean(string="Es etapa Relevamiento")
    is_etapa_analisis     = fields.Boolean(string="Es etapa Análisis de Crédito")
    is_etapa_servicio     = fields.Boolean(string="Es etapa Servicio Técnico")

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    genera_cotizador       = fields.Boolean(string="Genera Cotizador?", compute="_compute_generar_cotizador", store=True)
    presale_ricoh_id       = fields.One2many('presale.ricoh.order', 'lead_id', string="Presale Ricoh", track_visibility='onchange')
    is_etapa_contacto      = fields.Boolean(related='stage_id.is_etapa_contacto', string="Está en Contacto", store=True)
    is_etapa_relevamiento  = fields.Boolean(related='stage_id.is_etapa_relevamiento', string="Está en Relevamiento", store=True)
    is_etapa_analisis      = fields.Boolean(related='stage_id.is_etapa_analisis', string="En Análisis de Crédito", store=True)
    is_rch                 = fields.Boolean(string="Unidad es RCH", compute="_compute_is_rch", store=True)
    presale_count          = fields.Integer(string="Cotizaciones", compute="_compute_presale_count")
    has_presale            = fields.Boolean(string="Tiene Preventas", compute="_compute_has_presale")
    credit_state           = fields.Selection([('pending','Pendiente'),('correction','En Corrección'),('approved','Aprobada')], string="Estado Crédito", default='pending', copy=False, tracking=True)
    credit_reason          = fields.Text(string="Motivo Corrección", copy=False, help="Razón por la cual quedó en corrección")
    has_invoice_terms      = fields.Boolean(string="Tiene Términos Facturación", compute="_compute_has_invoice_terms")
    credit_attachment_ids  = fields.Many2many('ir.attachment', 'crm_lead_credit_attachment_rel', 'lead_id', 'attachment_id', string="Documentos de Crédito", copy=False)

    @api.depends('stage_id.genera_cotizador')
    def _compute_generar_cotizador(self):
        for rec in self:
            rec.genera_cotizador = bool(rec.stage_id.genera_cotizador)

    @api.depends('operating_unit')
    def _compute_is_rch(self):
        for lead in self:
            lead.is_rch = bool(lead.operating_unit and lead.operating_unit.code == 'RCH')

    @api.depends('presale_ricoh_id')
    def _compute_presale_count(self):
        for lead in self:
            lead.presale_count = self.env['presale.ricoh.order'].search_count([('lead_id', '=', lead.id)])

    @api.depends('presale_count')
    def _compute_has_presale(self):
        for lead in self:
            lead.has_presale = bool(lead.presale_count)

    @api.depends('presale_ricoh_id.presupuesto_id.invoice_term_ids')
    def _compute_has_invoice_terms(self):
        for lead in self:
            sale = lead.presale_ricoh_id.presupuesto_id
            lead.has_invoice_terms = bool(sale and sale.invoice_term_ids)

    def action_set_relevamiento(self):
        self.ensure_one()
        stage = self.env['crm.stage'].search([('is_etapa_relevamiento', '=', True)], limit=1)
        if stage:
            self.stage_id = stage.id

    def action_set_cotizacion(self):
        self.ensure_one()
        stage = self.env['crm.stage'].search([('genera_cotizador', '=', True)], limit=1)
        if stage:
            self.stage_id = stage.id

    def action_confirm_preventa(self):
        self.ensure_one()
        stage = self.env['crm.stage'].search([('name', '=', 'Preventa (Cotizador)')], limit=1)
        if stage:
            self.stage_id = stage.id
        seq = self.env['ir.sequence'].next_by_code('presale.order') or 'PS001'
        new_presale = self.env['presale.ricoh.order'].create({
            'name': "%s - %s" % (seq, self.name),
            'partner_id': self.partner_id.id or False,
            'lead_id': self.id,
            'equipo_de_venta': self.stage_id.team_id.name,
        })
        self.presale_ricoh_id = new_presale

    def action_view_presale_orders(self):
        self.ensure_one()
        if not self.presale_count:
            return {'type': 'ir.actions.act_window_close'}
        action = self.env.ref('presale_ricoh.action_presale_ricoh_order').read()[0]
        action['domain'] = [('lead_id', '=', self.id)]
        action['context'] = {'default_lead_id': self.id}
        return action

    def action_credit_approve(self):
        self.ensure_one()
        if not self.has_invoice_terms:
            raise UserError(_("Para aprobar, la Preventa debe tener al menos un término de facturación."))
        self.credit_state = 'approved'
        stage = self.env['crm.stage'].search([('is_etapa_servicio', '=', True)], limit=1)
        if stage:
            self.stage_id = stage.id

    def action_credit_reject(self):
        self.ensure_one()
        if not self.credit_reason:
            raise UserError(_("Debe especificar el motivo de la corrección."))
        self.credit_state = 'correction'

class PresaleOrder(models.Model):
    _inherit = 'presale.ricoh.order'

    def action_approve(self):
        res = super(PresaleOrder, self).action_approve()
        for order in self:
            if order.lead_id:
                stage = self.env['crm.stage'].search([('is_etapa_analisis', '=', True)], limit=1)
                if stage:
                    order.lead_id.stage_id = stage.id
                else:
                    _logger.warning("No existe etapa Análisis de Crédito")
        return res
