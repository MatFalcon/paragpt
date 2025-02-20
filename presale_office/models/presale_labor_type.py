from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class PresaleLaborType(models.Model):
    _name = 'presale.labor_type'
    _description = 'Presale labor types'

    name = fields.Char(string="Name", tracking=True, copy=True)

    @api.constrains('name')
    def _check_labor_type(self):
        for rec in self:
            labor_type = self.env['presale.labor_type'].search_count([('name', '=', rec.name)])
            if labor_type > 1:
                raise ValidationError(_('This name was already used for this type of labor!'))




