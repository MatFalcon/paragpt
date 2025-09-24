# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "product.template"

    es_mantenimiento_registro = fields.Boolean(string="Es Mantenimiento Registro", default=False)
    jornal = fields.Many2one('mantenimiento_registro.jornal_mantenimiento',
                             string="Jornal", domain=[('activo', '=', True)])
