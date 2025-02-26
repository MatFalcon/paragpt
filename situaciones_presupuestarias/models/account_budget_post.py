from odoo import _, api, fields, models, exceptions
from odoo.osv import expression
from collections import defaultdict
from datetime import timedelta


class AccountBudgetPost(models.Model):
    _inherit = 'account.budget.post'
    @api.model
    def createAccountBudgetPost(self, cuenta):
        if cuenta:
            vals = {
                'company_id': self.env.user.company_id.id,
                'name': cuenta.name,
                'account_ids':[(6, 0, cuenta.ids)]
            }
            self.env['account.budget.post'].create(vals)