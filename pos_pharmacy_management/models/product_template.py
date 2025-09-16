# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import fields, models, api
    
class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    is_pharma_product = fields.Boolean(string='Is a Pharma Product')
    is_medicine = fields.Boolean(string='Is a Medicine')
    is_prescription = fields.Boolean(string='Is Prescription Medicine')
    medicine_search_term = fields.Text(compute="_compute_search_terms", store=True)
    manufacturer_id = fields.Many2one('medicine.manufacturer', string='Manufacturer')
    salt_composition_ids = fields.Many2many('salt.composition', string='Salt Composition Synonyms')
    medicine_salt_ids = fields.Many2many('medicine.salt', string='Alternate of Salt')
    medicine_usage_ids = fields.Many2many('medicine.usage', string='Uses of Medicine')
    side_effects_ids = fields.Many2many('side.effects', string='Side Effects of Medicine')
    safety_advice_ids = fields.Many2many('safety.advice', string='Safety Advices of Medicine')
    fact_box_ids = fields.Many2many('fact.box', string='Fact Box')
    medicine_substitute_ids = fields.Many2many('product.product', 'substitutes', 'medicine', 'substitute',string='Alternate Medicine', domain="[('is_medicine', '=', True), ('product_tmpl_id.name', '!=', name)]")
    salt_ids = fields.Many2many('basic.salt', string='Interaction with Drugs')
    storage = fields.Float('Storage')
    manage_multi_uom_via_price = fields.Boolean(string='Manage Multi UOM Price')
    product_price_by_uom = fields.One2many('product.uom.price', 'variant', string='Product Price By UOM')

    @api.depends('manufacturer_id', 'medicine_usage_ids','salt_ids', 'medicine_salt_ids', 'salt_composition_ids')
    def _compute_search_terms(self):
        li=[]
        records = self.product_variant_id  
        for rec in records:
            if(rec.manufacturer_id):
                li.append(rec.manufacturer_id.name.lower())
            
            for ids in rec.medicine_usage_ids:
                li.append(ids.name.lower())
                
            for ids in rec.salt_composition_ids:
                li.append(ids.name.lower())
                
            for ids in rec.medicine_salt_ids:
                li.append(ids.name.lower())
                
            for ids in rec.salt_ids:
                li.append(ids.name.lower())
                
            self.medicine_search_term = '|'.join(li)
