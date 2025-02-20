from odoo import fields, models, exceptions, api , _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from lxml import etree
from datetime import datetime as dt
import logging

class PresaleTransfers(models.Model):
    _name = "presale.transfers"

    transfers_order_id = fields.Many2one('presale.order', string="Presale Order", store=True, copy=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string="Mobile", tracking=True, copy=True)
    transfers = fields.Float(string="Transfers")
    fuel_type = fields.Many2one('presale.fuel_type', string="Fuel Type")
    consumption_per_liter = fields.Float(string="Consume P/ Liter", compute="set_consumption_value", store=True, )
    distance_to_work = fields.Float(string="Distance to work")
    consumption_till_work = fields.Float(string="Consumption till Work", compute="calculate_transfer", store=True)
    price_per_liter = fields.Float(string="Price P/ Liter")
    price_per_tour = fields.Float(string="Price P/ Tour", compute="calculate_transfer", store=True)
    total_price_per_tour = fields.Float(string="Total Price P/ Tour", compute="calculate_transfer", store=True)
    toll = fields.Float(string="Toll")
    total_transfer_amount = fields.Float(string="Total x transfer amount", compute="calculate_transfer", store=True)


    @api.depends('vehicle_id.consumption_per_kilometer')
    def set_consumption_value(self):
        for rec in self:
            if rec.vehicle_id:
                rec.consumption_per_liter = rec.vehicle_id.consumption_per_kilometer
            else:
                rec.consumption_per_liter = None


    @api.onchange('vehicle_id.consumption_per_kilometer')
    def set_consumption_value_onchange(self):
        self.set_consumption_value()


    @api.depends('consumption_per_liter', 'distance_to_work', 'transfers', 'price_per_liter', 'toll')
    def calculate_transfer(self):
        for rec in self:
            rec.consumption_till_work = rec.distance_to_work * 2 * rec.consumption_per_liter
            rec.price_per_tour = rec.price_per_liter * rec.consumption_till_work
            rec.total_price_per_tour = rec.price_per_tour * rec.transfers
            rec.total_transfer_amount = rec.total_price_per_tour + rec.toll