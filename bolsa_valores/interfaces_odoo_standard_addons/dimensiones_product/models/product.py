from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    ancho = fields.Float(string="Ancho", default=0)
    largo = fields.Float(string="Largo", default=0)
    alto = fields.Float(string="Alto", default=0)

