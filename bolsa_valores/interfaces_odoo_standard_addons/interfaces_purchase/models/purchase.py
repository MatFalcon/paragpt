from odoo import fields, api, models, exceptions


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    nro_despacho = fields.Char(string="Nro Despacho")
