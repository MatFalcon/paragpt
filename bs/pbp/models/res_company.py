from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    banco_sudameris_nro_cuenta_pyg = fields.Char(string='Nro Cuenta SUDAMERIS PYG')
    banco_sudameris_nro_cuenta_usd = fields.Char(string='Nro Cuenta SUDAMERIS USD')
    banco_sudameris_cod_contrato = fields.Char(string='Nro Contrato SUDAMERIS')
    banco_sudameris_email_asociado = fields.Char(string='Email Asociado SUDAMERIS')
