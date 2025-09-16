# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class MedicineManufacturer(models.Model):
    _name = 'medicine.manufacturer'
    _description = 'Medicine Manufacturer'

    name = fields.Char('Name', required=True)
    parent_id = fields.Many2one('medicine.manufacturer', 'Parent Category', index=True)

class Diseases(models.Model):
    _name = 'disease.disease'
    _description = 'Diseases'

    name = fields.Char('Name', required=True)
    disease = fields.Text('Description')

class BasicSalt(models.Model):
    _name = 'basic.salt'
    _description = 'Basic Medicine Salt'
    
    name = fields.Char('Basic Salt', required=True)

class SaltUnit(models.Model):
    _name = 'salt.unit'
    _description = 'Medicine Salt Unit'
    _rec_name = "salt_unit"
    
    salt_unit = fields.Char('Salt Unit', required=True)

class MedicineSalt(models.Model):
    _name = 'medicine.salt'
    _description = 'Medicine Salt'
    
    name = fields.Char('Medicine Salt', required=True)
    salt = fields.Many2one('basic.salt', 'Basic Salt')
    qty = fields.Float('Quantity')
    unit = fields.Many2one('salt.unit', 'Salt Unit')
    medicine_salt_ids = fields.Many2many('medicine.salt', 'salt_synonyms', 'medicine_salt_1', 'medicine_salt_2', 'Salt Synonyms')
        
    @api.onchange('name', 'unit')
    def compute_name(self):
        if self.name and self.unit:
            name = self.name.split("(")[0]
            self.name = "{0}({1})".format(name, self.unit.salt_unit)

class SaltComposition(models.Model):
    _name = 'salt.composition'
    _description = 'Salt Composition'
    
    name = fields.Char(string="Salt Composition", required=True)
    medicine_salt_ids = fields.Many2many('medicine.salt', string='Salts')
    salt_composition_ids = fields.Many2many('salt.composition', 'salt_composition_synonyms', 'salt_composition_1', 'salt_composition_2', 'Salt Composition Synonyms')

class MedicineUsage(models.Model):
    _name = 'medicine.usage'
    _description = 'Medicine Usage'
    
    name = fields.Char('Name', required=True)
    medicine_usage = fields.Text('Medicine Usage')

class SideEffects(models.Model):
    _name = 'side.effects'
    _description = 'Side Effects of Medicine'
    
    name = fields.Char('Name', required=True)
    side_effects = fields.Text('Side Effect')

class SafetyAdvice(models.Model):
    _name = 'safety.advice'
    _description = 'Safety Advice'

    name = fields.Char('Name', required=True)
    safety_advice = fields.Text('Safety Advice')

class ChecmicalClass(models.Model):
    _name = 'chemical.class'
    _description = 'Medicine Chemical Class'
    
    name = fields.Char('Name', required=True)

class TherapeuticClass(models.Model):
    _name = 'therapeutic.class'
    _description = 'Medicine Therapeutic Class'
    
    name = fields.Char('Name', required=True)

class ActionClass(models.Model):
    _name = 'action.class'
    _description = 'Medicine Action Class'
    
    name = fields.Char('Name', required=True)

class FactBox(models.Model):
    _name = 'fact.box'
    _description = 'Fact Box'

    name = fields.Char('Name', required=True)
    habit_forming = fields.Boolean('Habit Forming', required=True)
    chemical_class = fields.Many2one('chemical.class', 'Chemical Class')
    therapeutic_class = fields.Many2one('therapeutic.class', 'Therapeutic Class')
    action_class = fields.Many2one('action.class', 'Action Class')

class ProductUOMPrice(models.Model):
    _name = 'product.uom.price'
    _description = 'Product UOM Price'

    variant = fields.Many2one('product.template', 'Product')
    uom_id = fields.Many2one('uom.uom', 'UOM', required=True, domain=[('category_id.is_medicine', '=', True)])
    qty = fields.Float('Qty')
    unit_price = fields.Float('Unit Price')
    price = fields.Float("Price", readonly=True, compute="_compute_price")

    @api.model
    def create(self, vals):
        variant_id = vals.get("variant")
        uom_id = vals.get("uom_id")
        qty = vals.get("qty")

        # Ensure the search includes the current product (variant)
        existing_lines = self.search(
            [("variant", "=", variant_id), ("uom_id", "=", uom_id)]
        )
        for line in existing_lines:
            if line.qty == qty:
                raise UserError(
                    "A line with the same UOM and Qty already exists for this product."
                )

        return super(ProductUOMPrice, self).create(vals)

    def write(self, vals):
        for record in self:
            variant_id = vals.get("variant", record.variant.id)
            uom_id = vals.get("uom_id", record.uom_id.id)
            qty = vals.get("qty", record.qty)

            # Ensure the search includes the current product (variant)
            existing_lines = self.search(
                [
                    ("variant", "=", variant_id),
                    ("uom_id", "=", uom_id),
                    ("id", "!=", record.id),
                ]
            )
            for line in existing_lines:
                if line.qty == qty:
                    raise UserError(
                        "A line with the same UOM and Qty already exists for this product."
                    )

        return super(ProductUOMPrice, self).write(vals)

    @api.depends("qty", "unit_price")
    def _compute_price(self):
        for record in self:
            if record.qty and record.unit_price:
                record.price = record.qty * record.unit_price
            else:
                record.price = 0.0


class UomCategory(models.Model):
    _inherit = 'uom.category'
    
    is_medicine = fields.Boolean('Is a Medicine')
