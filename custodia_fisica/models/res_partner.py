# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    arancel_cantidad_id = fields.Many2one(
        'custodia_fisica.aranceles_cantidad', string="Arancel de cantidad")
    arancel_monto_id = fields.Many2one(
        'custodia_fisica.aranceles_monto', string="Arancel de monto")
    geene_api_pk = fields.Char(
        string="Clave geene API")
