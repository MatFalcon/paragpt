from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class PresaleLaborProduct(models.Model):
    _name = 'presale.labor_product'
    _description = 'Presale labor for products matrix'

    name = fields.Char(string="Name")
    labor_type_id = fields.Many2one('presale.labor_type','Labor type')
    product_id = fields.Many2one('product.template','Product')
    amount = fields.Float(string="Amount",digits=(12,3))
    # corr_factor = fields.Boolean('Correction Factor', default=False)

    @api.constrains('product_id','labor_type_id')
    def _check_labor_product(self):
        for rec in self:
            currency_rates = self.env['presale.labor_product'].search_count(
                [('product_id', '=', rec.product_id.id), ('labor_type_id', '=', rec.labor_type_id.id),
                 ('id', '!=', rec.id)])
            if currency_rates >= 1:
                raise ValidationError(_('A conf already exist for this product and labor type'))

    @api.model
    def create(self, vals):
        res = super(PresaleLaborProduct, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('presale.labor_product_sequence')
        return res

# class ProductProduct(models.Model):
#     _inherit = 'product.template'
#
#     labor_product_ids = fields.One2many('presale.labor_product','product_id',string="Labors")

