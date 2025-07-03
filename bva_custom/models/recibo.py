# -*- coding: UTF-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, time, timedelta

class ReciboCobranza(models.Model):
    _inherit = 'account.recibo'

    correo_enviado = fields.Boolean(string="Correo enviado")

    @api.model
    def enviarRecibosDia(self):
        hoy = date.today()
        hace_un_anho = hoy - relativedelta(years=1)
        recibos_todo = self.env['account.recibo'].search([('state', '=', 'confirmado'),
                                                     ('correo_enviado', '!=', True),
                                                     ('fecha', '<=', date.today()),
                                                     ('fecha', '>', hace_un_anho)])


        recibos = recibos_todo.filtered(lambda r: not any(p.correo_enviado for p in r.payment_ids))

        for r in recibos:
            template = self.env.ref('bva_custom.mail_template_data_recibo_pago')
            destinatarios = [r.partner_id.id]
            copias = self.env.user.company_id.partner_id.email + ', '
            if r.partner_id.child_ids:
                for c in r.partner_id.child_ids.filtered(lambda x: x.email):
                    copias += c.email + ', '
            if destinatarios:
                vals = {
                    'recipient_ids': destinatarios,
                    'email_from': self.env.user.company_id.email,
                    'author_id': self.env.user.id,
                    'email_cc': copias,
                }
                template.send_mail(r.id, email_values=vals, force_send=True)
                r.write({'correo_enviado': True})
