from odoo import fields,models,api,exceptions

class AccountBankStatementLine(models.Model):
    _inherit='account.bank.statement.line'

    payment_id=fields.Many2one('account.payment')