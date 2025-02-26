# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    es_custodia_fisica = fields.Boolean(
        string="Es emisión de custodia física", default=False)
    geene_api_pk = fields.Char(
        string="Clave geene API")
