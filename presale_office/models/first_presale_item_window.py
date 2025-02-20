from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class InheritPresaleOrder(models.Model):
    _inherit = 'presale.order'

    first_item_ids = fields.One2many('first.item.window', 'presale_id', string="First Item")

class ItemWindow(models.Model):
    _name = 'first.item.window'

    name = fields.Char(string="Name")
    #heading_ids = fields.One2many('presale.order.heading','first_item_id',string="Items", copy=True)
    presale_id = fields.Many2one('presale.order')

class InheritPresaleItem(models.Model):
    _inherit='presale.order.item.detail'

    order_heading_id = fields.Many2one('presale.order.heading')

class InheritPresaleHeading(models.Model):
    _inherit = 'presale.order.heading'

    first_item_id = fields.Many2one('first.item.window')
    order_detail_id = fields.One2many('presale.order.item.detail', 'order_heading_id')

    gastos_porcentaje_10 = fields.Float(string="(10%)")
    gastos_porcentaje_20 = fields.Float(string="(20%)")

    gastos_def_10 = fields.Float(string="Gastos Administrativos (10%)", tracking=True, copy=True, compute='calcular_gastos_administrativos')
    gastos_def_20 = fields.Float(string="Gastos Administrativos (20%)", tracking=True, copy=True, compute='calcular_gastos_administrativos')
    unit_cost_total = fields.Float(string="Precio Total Unitario", tracking=True, copy=True, compute='calcular_gastos_administrativos')
    total_cost = fields.Float(string="Precio Total", tracking=True, copy=True, compute='calcular_gastos_administrativos')

    @api.depends('gastos_porcentaje_10', 'gastos_porcentaje_20', 'item_id.detail_ids.unit_cost')
    def calcular_gastos_administrativos(self):
        self.gastos_def_10 = 0
        self.unit_cost_total = 0
        self.gastos_def_20 = 0
        self.total_cost = 0
        for r in self:
            r.gastos_def_10 = sum(r.item_id.detail_ids.mapped('unit_cost')) * (r.gastos_porcentaje_10 / 100)
            r.gastos_def_20 = sum(r.item_id.detail_ids.mapped('unit_cost')) * (r.gastos_porcentaje_20 / 100)
            r.unit_cost_total = sum(r.item_id.detail_ids.mapped('unit_cost')) + r.gastos_def_20 + r.gastos_def_10