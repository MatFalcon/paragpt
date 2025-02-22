from odoo import models,fields,api,exceptions


class ResPartner(models.Model):
    _inherit = 'res.partner'


    property_ext_account_receivable_id=fields.Many2one('account.account',string="Cuentas a cobrar (Moneda extranjera)")
    property_ext_account_payable_id=fields.Many2one('account.account',string="Cuentas a pagar (Moneda extranjera)")

