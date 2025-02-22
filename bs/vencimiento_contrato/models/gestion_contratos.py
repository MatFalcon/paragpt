from odoo import models, fields, api, exceptions
from datetime import datetime, date
import xlrd
import base64


class GestionContratos(models.Model):
    _name = 'vencimiento_contrato.gestion_contrato'

    name = fields.Many2one('res.partner', string="Contratado")
    nombre_contrato = fields.Char(string="Nombre de Contrato")
    fecha_inicio = fields.Date(string="Fecha de inicio", required=True, default=lambda self: fields.Date.today())
    fecha_fin = fields.Date(string="Fecha de fin", required=True, default=lambda self: fields.Date.today())
    fecha_fin_aux = fields.Date(string="Fecha de fin auxiliar")
    state = fields.Selection(string="Estado",
                             selection=[('vencido', 'Vencido'), ('vigente', 'Vigente'), ('por_iniciar', 'Por iniciar')],
                             compute="vigencia", store=True)
    contrato_indefinido = fields.Boolean(string="Contrato indefinido")

    @api.onchange('contrato_indefinido')
    def onch_contrato_indefinido(self):
        for this in self:
            if this.contrato_indefinido:
                this.fecha_fin_aux = this.fecha_fin
                this.fecha_fin = date(2100, 12, 31)
            else:
                this.fecha_fin = this.fecha_fin_aux
        self.vigencia()

    @api.onchange('fecha_fin', 'fecha_inicio')
    def vigencia(self):
        for this in self:
            if this.name._origin.id == False or not this.fecha_fin:
                return
            # cont = self.env['vencimiento_contrato.gestion_contrato'].search(
            #     [('name', '=', this.name._origin.id)])
            if this.fecha_fin >= date.today():
                if this.fecha_inicio > date.today():
                    this.update({
                        'state': 'por_iniciar'
                    })
                else:
                    this.update({
                        'state': 'vigente'
                    })
            else:
                this.update({
                    'state': 'vencido'
                })

    @api.model
    def cron_vigencia(self):
        contactos = self.env['res.partner'].search([('con_contrato', '=', True), ('contratos_ids', '!=', False)])
        for contacto in contactos:
            contratos = contacto.mapped('contratos_ids').filtered(lambda x: x.state != 'vencido')
            cont_sort = contratos.sorted(key=lambda x: x.fecha_fin)
            for c in cont_sort:
                if c.fecha_fin >= date.today():
                    if c.fecha_inicio > date.today():
                        c.write({
                            'state': 'por_iniciar'
                        })
                    else:
                        c.write({
                            'state': 'vigente'
                        })
                else:
                    c.write({
                        'state': 'vencido'
                    })

    @api.model
    def cron_notificaciones(self):
        contratados = self.env['res.partner'].search([('con_contrato', '=', True), ('contratos_ids', '!=', False)])
        contratados_filtrados = contratados.filtered(
            lambda x: not x.contratos_ids.filtered(lambda z: z.state == 'por_iniciar') and x.contratos_ids.filtered(
                lambda z: z.state == 'vigente'))
        contratos_a_vencer = contratados_filtrados.mapped('contratos_ids').filtered(lambda x:x.state == 'vigente')
        destinatarios = []
        for contr in contratos_a_vencer:
            dif60 = contr.fecha_fin - date.today()
            if dif60.days in [60, 53, 46, 39, 32, 25, 18, 11, 4]:
                destinatarios.append(self.env.user.company_id.partner_id.id)
                template = self.env.ref('vencimiento_contrato.mail_template_vencimientos_contrato')

                vals = {
                    'email_from': 'administracion@bolsadevalores.com.py',
                    'author_id': self.env.user.id,
                    'subject': 'Re: Vencimiento del Contrato "%s" a fecha %s' % (contr.nombre_contrato, contr.fecha_fin),
                    'auto_delete': False,
                    'recipient_ids': destinatarios
                }
                mail_id = template.send_mail(contr.id, email_values=vals, force_send=True)

    def create(self, vals):
        resp = super(GestionContratos, self).create(vals)
        resp.vigencia()
        return resp
