from odoo import models, fields


class AccountAccount(models.Model):
    _inherit = 'account.account'
    saldo = fields.Float(string='saldo')
    total_debe = fields.Float(string='total debe')
    total_haber = fields.Float(string='total haber')
    agregar_asiento = fields.Boolean(string='Agregar cuenta al asiento')
    total_divisas = fields.Float(string='Total de monto divisas')