from odoo import _, api, fields, models




class ResCompany(models.Model):
    _inherit = 'res.company'

    secondary_currency_id=fields.Many2one('res.currency',string="Moneda secundaria")