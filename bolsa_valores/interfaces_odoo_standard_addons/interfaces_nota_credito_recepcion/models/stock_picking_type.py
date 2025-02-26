from odoo import models, fields


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    move_type_2 = fields.Selection(string='Tipo de factura', selection=[('in_refund', 'Proveedor'), ('out_refund', 'Cliente'),])
    