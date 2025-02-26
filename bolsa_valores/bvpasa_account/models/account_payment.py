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
            destinatarios = [r.partner_id.id]
            copias = self.env.user.company_id.partner_id.email + ', '
            if r.partner_id.child_ids:
                for c in r.partner_id.child_ids.filtered(lambda x: x.email):
                    copias += c.email + ', '
            if destinatarios:
                vals = {
                    'recipient_ids':destinatarios,
                    'email_from': self.env.user.company_id.email,
                    'author_id': self.env.user.id,
                    'email_cc': copias,
                }
                template.send_mail(r.id, email_values=vals, force_send=True)
                r.write({'correo_enviado':True})
