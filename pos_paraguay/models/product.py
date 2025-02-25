# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountMoveLineInherit(models.Model):
    _inherit = 'product.product'

class Product(models.Model):
    _inherit = 'product.product'

    tax_pos = fields.Char("Impuesto para Ticket", compute="_compute_tax", store=True)

    @api.depends("tax_pos")
    def _compute_tax(self):
        for record in self:
            tax_name = record.product_tmpl_id.taxes_id.name
            record.tax_pos = tax_name
            print("tax_name")
            print(tax_name)

