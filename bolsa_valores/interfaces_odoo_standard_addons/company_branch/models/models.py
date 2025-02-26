from odoo import models, fields


class CompanyCustom(models.Model):
    _inherit = 'res.company'

    branches = fields.One2many('company_branch.company_branch', 'company_id', 'Branches')


class CompanyBranch(models.Model):
    _name = 'company_branch.company_branch'

    name = fields.Char(required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True)
