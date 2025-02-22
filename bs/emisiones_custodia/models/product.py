# -*- coding: utf-8 -*-

from odoo import api, fields, models


class Product(models.Model):
    _inherit = "product.template"

    es_custodia = fields.Boolean(string="Es custodia", default=False)
    es_emision = fields.Boolean(string="Es emisión", default=False)
    es_bono = fields.Boolean(string="Es bono", default=False)
