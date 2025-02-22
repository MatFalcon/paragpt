from dataclasses import field
from odoo import models,fields,api,exceptions


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    receivable_account_id=fields.Many2one('account.account',company_dependent=True,string="Cuenta a cobrar moneda extranjera",domain=[('user_type_id.type','=','receivable')])
    payable_account_id=fields.Many2one('account.account',company_dependent=True,string="Cuenta a pagar moneda extranjera",domain=[('user_type_id.type','=','payable')])
