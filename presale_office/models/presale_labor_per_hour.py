from odoo import fields, models, exceptions, api , _
from odoo.exceptions import ValidationError

class presale_labor_per_hour(models.Model):
    _name = "presale.labor_per_hour"

    labor_type = fields.Many2one('presale.labor_type', string="Labor type", copy=True)

