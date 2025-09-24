import datetime

from odoo import models, fields, api, exceptions


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    correo_enviado = fields.Boolean(string="Correo Enviado", default=False, copy=False, tracking=True)

    @api.model
    def enviarRecibosDia(self):
        recibos = self.env['account.payment'].search([('state','=','posted'),
                                                      ('payment_type','=','inbound'),
                                                      ('correo_enviado','=',False),
                                                      ('date','<=',datetime.date.today()),
                                                      ('date','>','2024-01-15')])
        for r in recibos.filtered(lambda x: x.is_matched):
            template = self.env.ref('account.mail_template_data_payment_receipt')
            destinatarios = r.mapped('partner_id.child_ids.id')
            destinatarios.append(r.partner_id.id)
            destinatarios.append(self.env.user.company_id.partner_id.id)
            if destinatarios:
                vals = {
                    'recipient_ids':destinatarios,
                    'email_from': self.env.user.company_id.email,
                    'author_id': self.env.user.id
                }
                template.send_mail(r.id, email_values=vals, force_send=True)
                r.write({'correo_enviado':True})
