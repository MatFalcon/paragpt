# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api , _
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError


class PresaleProduct(models.Model):
    _inherit = 'product.template'

    is_minor_material = fields.Boolean(string="Is Minor Material?", defaul=False, copy=True)
    is_labour = fields.Boolean(string="Is Labour", default=False, copy=True)
    product_brand = fields.Many2one('product.brand', string="Product Brand", copy=True)

    @api.constrains('is_minor_material')
    def _check_minor_material(self):
        if self.is_minor_material:
            # count_minor_material = self.env['product.template'].search_count([('is_minor_material', '=', True), ('company_id', '=', self.env.user.company_id.id)])
            count_minor_material = self.env['product.template'].search_count([('is_minor_material', '=', True)])
            if count_minor_material > 1:
                raise ValidationError("Only 1 product with 'Minor Material' characteristics can exist")
            

    @api.constrains('is_labour')    
    def _check_labour(self):
        if self.is_labour:
            # count_labour_product = self.env['product.template'].search_count([('is_labour', '=', True),('company_id', '=', self.env.user.company_id.id)])
            count_labour_product = self.env['product.template'].search_count([('is_labour', '=', True)])
            if count_labour_product > 1:
                raise ValidationError("Only 1 product with 'Labour' characteristics can exist!")
            
    
    @api.onchange('is_minor_material', 'is_labour')
    def set_unset_boolean_fields(self):
        if self.is_minor_material:  
            self.is_labour = False
        
        if self.is_labour:
            self.is_minor_material = False  

            
            
class ProductBrand(models.Model):
    _name = 'product.brand'

    name = fields.Char(string="Product Brand")