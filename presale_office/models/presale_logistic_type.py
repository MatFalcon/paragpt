from odoo import fields, models, exceptions, api , _
from odoo.exceptions import ValidationError

class presale_logistic_type(models.Model):
    _name = 'presale.logistic_type'

    name = fields.Char(string="Name", tracking=True, copy=True)

    @api.constrains('name')
    def _check_logistic_type(self):
        for rec in self:
            labor_type = self.env['presale.logistic_type'].search_count([('name', '=', rec.name)])
            if labor_type > 1:
                raise ValidationError(_('This name was already used for this type of logistic!'))