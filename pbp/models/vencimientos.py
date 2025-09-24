from ast import literal_eval
from datetime import timedelta

from odoo import fields, models, api


class Vencimientos(models.TransientModel):
    _name = "pbp.vencimiento_capital_interes"
    _description = "Vencimiento de Capital e Intereses"

    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento")
    destinatarios = fields.Many2many('res.users', string="Destinatarios")
    registros = fields.Many2many('pbp.cartera_inversion', string="Capital e Intereses")
    texto = fields.Html(string="Texto")
    email_to = fields.Char(string="Destinatarios")
    user_id = fields.Many2one(
        'res.users', string="Usuario", required=True, default=lambda self: self.env.user)
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)

    @api.model
    def getEmailData(self):
        texto = ""
        destinatarios = []

        fecha_vencimiento = fields.Date.today() + timedelta(days=1)
        group = self.env['res.groups'].search([('name', '=', 'Grupo PBP')])
        #Si el grupo existe, busca los usuarios que pertenecen a él
        if group:
            users = self.env['res.users'].search([('groups_id', 'in', group.ids)])
        #    for u in users:
        #        email_to = email_to + u.email + ','

        destinatarios.append(self.env.user.company_id.partner_id.id)

        registros = self.env['pbp.cartera_inversion'].search([('fecha_vencimiento','=',fecha_vencimiento)])

        if registros:
            partners = set(registros.mapped('partner_id'))
            for p in partners:
                texto = texto + '<b>' + p.name + '</b><br/>'
                texto = texto + '<table><tr><td style="border:1px solid black;padding:5px">Emisor</td><td style="border:1px solid black;padding:5px">Fecha de vencimiento</td><td style="border:1px solid black;padding:5px">Instrumento</td><td style="border:1px solid black;padding:5px">Monto Intereses</td><td style="border:1px solid black;padding:5px">Serie</td><td style="border:1px solid black;padding:5px">Moneda</td></tr>'
                for r in registros.filtered(lambda x: x.partner_id == p):
                    texto = texto + '<tr><td style="border:1px solid black;padding:5px">' + r.partner_id.name +\
                            '</td><td style="border:1px solid black;padding:5px">'+ r.fecha_vencimiento.strftime("%d/%m/%Y") +\
                            '</td><td style="border:1px solid black;padding:5px">'+r.instrumento+\
                            '</td><td style="border:1px solid black;padding:5px">'+ str('{0:,.0f}'.format(r.intereses)).replace(",",".")+\
                            '</td><td style="border:1px solid black;padding:5px">'+r.serie + \
                            '</td><td style="border:1px solid black;padding:5px">'+r.currency_id.name + \
                            '</td></tr>'
                texto = texto + '</table>'

            registro_values = {
                'fecha_vencimiento':fecha_vencimiento,
                'destinatarios':[(6, 0, users.ids)],
                'registros': [(6, 0, registros.ids)],
                'texto':texto
            }

            vencimiento_capital_interes = self.env['pbp.vencimiento_capital_interes'].create(registro_values)

            template = self.env.ref('pbp.mail_template_vencimientos_capital_interes')

            vals = {
                'email_from': 'tesoreria@bolsadevalores.com.py',
                'author_id': self.user_id.id,
                'subject': 'Re: Vencimiento de Capital e Interes a fecha %s' % fecha_vencimiento,
                'auto_delete': False,
                'recipient_ids': destinatarios
            }
            mail_id = template.send_mail(vencimiento_capital_interes.id, email_values=vals, force_send=True)
            for r in registros:
                r.write({'correo_enviado': True, 'mail_id': mail_id})




