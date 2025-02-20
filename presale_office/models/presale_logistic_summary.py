from odoo import fields, models, exceptions, api , _
from odoo.exceptions import ValidationError

class presale_logistic_summary(models.Model):
    _name = 'presale.logistic_summary'

    order_id_log = fields.Many2one('presale.order', 'Presale Order', copy=True)
    type_logistic = fields.Many2one('presale.logistic_type', string="Type Logistic", tracking=True, copy=True)
    time_month = fields.Float(string="Time/Month", tracking=True, copy=True)
    unit_cost = fields.Float(string="Unit Cost", tracking=True, copy=True)
    total_cost = fields.Float(string="Total Cost", compute="calculate_logistic", store=True, copy=True)

    @api.depends('time_month','unit_cost')
    def calculate_logistic(self):
        for rec in self:
            rec.total_cost = rec.unit_cost * rec.time_month

