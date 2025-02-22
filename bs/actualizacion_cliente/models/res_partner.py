from datetime import datetime, date

from odoo import models, fields, api, exceptions


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ultima_actualizacion = fields.Date(string="Ultima actualizacion de datos")
    registro_actualizacion = fields.Boolean(string="Registro de actualizacion", default=False)

    @api.model
    def cron_notificaciones(self):
        contactos = self.env['res.partner'].search([('registro_actualizacion', '=', True), ('ultima_actualizacion', '!=', False)])
        destinatarios = []
        for con in contactos:
            envio_correo = False
            if con.registro_actualizacion and con.ultima_actualizacion:
                dif30 = date.today() - con.ultima_actualizacion
                if (dif30.days - 365) in [30, 23, 16, 9, 2]:
                    envio_correo = True
                elif dif30.days > 365 and (dif30.days - 365) % 7 == 0:
                    envio_correo = True

                if envio_correo:
                    destinatarios.append(self.env.user.company_id.partner_id.id)
                    template = self.env.ref('actualizacion_cliente.mail_template_actualizacion_cliente')

                    vals = {
                        'email_from': 'administracion@bolsadevalores.com.py',
                        'author_id': self.env.user.id,
                        'subject': 'Re: Ultima actualizacion de datos de %s (%s)' % (con.name, con.ultima_actualizacion),
                        'auto_delete': False,
                        'recipient_ids': destinatarios
                    }
                    mail_id = template.send_mail(con.id, email_values=vals, force_send=True)
