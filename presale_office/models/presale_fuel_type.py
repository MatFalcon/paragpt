from odoo import fields, models, exceptions, api , _
from odoo.exceptions import ValidationError

class presale_fuel_type(models.Model):
        _name = "presale.fuel_type"

        name = fields.Char(string="Name", tracking=True, copy=True)
        consumption_rate = fields.Float(string="Consumption Rate", tracking=True, copy=True)

        @api.constrains('name')
        def _check_fuel_type(self):
            for rec in self:
                fuel_type = self.env['presale.fuel_type'].search_count([('name', '=', rec.name)])
                if fuel_type > 1:
                    raise ValidationError(_('This name was already used for this type of logistic!'))