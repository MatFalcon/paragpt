from odoo import models, fields


class UsersCustom(models.Model):
    _inherit = 'res.users'

    company_branch_id = fields.Many2one('company_branch.company_branch', string='Company Branch')
    company_branch_ids = fields.Many2many('company_branch.company_branch', 'company_branch_users_rel', 'user_id', 'bid',
        string='Company Branches')
