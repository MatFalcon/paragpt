from odoo import models, fields, api, exceptions


class ProductProduct(models.Model):
    _inherit = "product.template"

    list_price_ext = fields.Float(
        'Precio de venta ext', company_dependent=True,
        digits='Product Price')
