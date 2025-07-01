from odoo import models, fields, api

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    # Campos para mantener trazabilidad con la preventa
    presale_item_id = fields.Many2one('presale.ricoh.order.item', string='Presale Item', readonly=True)
    presale_detail_id = fields.Many2one('presale.ricoh.order.item.detail', string='Presale Detail', readonly=True)
    
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Campo para mantener la relacion con la preventa
    presale_ricoh_id = fields.Many2one('presale.ricoh.order', string='Preventa Ricoh', readonly=True)