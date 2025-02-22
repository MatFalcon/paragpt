from odoo import _, api, fields, models, exceptions
from odoo.osv import expression
from collections import defaultdict
from datetime import timedelta


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(AccountAccount, self).create(vals_list)
        if res:
            self.env['account.budget.post'].createAccountBudgetPost(res)
        return res
