
# -*- coding: utf-8 -*-

from odoo import fields, models, api


class ResCity(models.Model):
    _inherit = 'res.city'

    id_pagopar = fields.Integer('ID en pagopar')

    def get_website_sale_cities(self):
        return self.sudo().search([])