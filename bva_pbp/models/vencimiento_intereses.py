from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class VencimientoLiquidaciones(models.TransientModel):
    _name = "pbp.vencimiento_interes"
    _description = "Vencimiento de Intereses"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento")
    destinatarios = fields.Many2many('res.users', string="Destinatarios")
    registros = fields.Many2many('pbp.liquidaciones', string="Liquidaciones")
    texto = fields.Html(string="Texto")
    email_to = fields.Char(string="Destinatarios")
    user_id = fields.Many2one(
        'res.users', string="Usuario", required=True, default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one('res.partner', string="Cliente", required=True, tracking=True)

    @api.model
    def getEmailData(self):
        fecha_vencimiento = fields.Date.today()

        registros = self.env['pbp.liquidaciones'].search([('fecha_vencimiento', '=', fecha_vencimiento),('correo_enviado','=',False)])

        if registros:
            partners = set(registros.mapped('partner_id'))
            monedas = set(registros.mapped('currency_id'))
            for p in partners:
                texto = ""
                destinatarios = p.mapped('child_ids.id')
                destinatarios.append(p.id)
                destinatarios.append(self.env.user.company_id.partner_id.id)
                texto = texto + '<table style="margin-left:50px;"><tr style="border-bottom:1px solid #bfbfbf"><td style="padding:5px;font-weight:bold">' + p.name + '</td></tr>'
                for m in monedas:
                    rm = registros.filtered(lambda x: x.partner_id == p and x.currency_id == m)
                    suma = sum(rm.mapped('monto'))
                    if suma != 0:
                        if m.name == "PYG":
                            texto = texto + '<tr><td style="padding:10px;font-weight:bold">' + m.name + '</td><td style="padding:5px;font-weight:bold;text-align:right">' + str(
                                '{0:,.0f}'.format(suma)).replace(",", ".") + '<td/><tr/>'
                            for r in rm:
                                texto = texto + '<tr><td style="padding:10px">' + r.serie + '<td style="padding:5px;text-align:right">' + str(
                                    '{0:,.0f}'.format(r.monto)).replace(",", ".") + '<td/><tr/>'
                        else:
                            moneda_name = m.name
                            if moneda_name.find('-') > 0:
                                moneda_name = moneda_name[0:moneda_name.find('-')]
                            texto = texto + '<tr><td style="padding:10px;font-weight:bold">' + moneda_name + '</td><td style="padding:5px;font-weight:bold;text-align:right">' + str(
                                '{0:,.2f}'.format(suma)) + '<td/><tr/>'
                            for r in rm:
                                texto = texto + '<tr><td style="padding:10px">' + r.serie + '<td style="padding:5px;text-align:right">' + str(
                                    '{0:,.2f}'.format(r.monto)) + '<td/><tr/>'
                texto = texto + '</table>'

                registro_values = {
                    'fecha_vencimiento': fecha_vencimiento,
                    'registros': [(6, 0, registros.ids)],
                    'texto': texto,
                    'partner_id':p.id
                }

                vencimiento_interes = self.env['pbp.vencimiento_interes'].create(registro_values)

                template = self.env.ref('pbp.mail_template_vencimientos_interes')

                vals = {
                    'email_from': 'administracion@bolsadevalores.com.py',
                    'author_id': self.env.user.partner_id.id,
                    'subject': 'Vencimiento de Interes a Fecha ' + fecha_vencimiento.strftime("%d/%m/%Y"),
                    'auto_delete': False,
                    'recipient_ids': destinatarios
                }
                mail_id = template.send_mail(vencimiento_interes.id, email_values=vals, force_send=True)
                for r in registros.filtered(lambda x: x.partner_id == p):
                    r.write({'correo_enviado': True, 'mail_id': mail_id})
