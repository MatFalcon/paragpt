# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import fields, models
    
class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    add_menu_bar = fields.Boolean('Add a Menu Bar', default=True)
    advance_search = fields.Boolean('Advance Search', default=True)
    product_display_type = fields.Selection([ ('list', 'List View'),('grid', 'Grid View'),], 'Product Display Type', default="list", required=True)
    show_medicine_information = fields.Boolean('Show Medicine Information', default=True)
    show_details_in_products = fields.Boolean('Show Details in Products', default=True)
    manufacturer = fields.Boolean('Manufacturer')
    storage = fields.Boolean('Storage')
    usage = fields.Boolean('Uses of Medicine')
    salt_alternate = fields.Boolean('Salt Alternate')
    salt_composition = fields.Boolean('Salt Composition')
    substitute = fields.Boolean('Substitute')
    side_effects = fields.Boolean('Side Effects')
    safety_advice = fields.Boolean('Safety Advice')
    basic_salt = fields.Boolean('Basic Salt')
    delete_order = fields.Boolean('Delete Order Button', default=True)
    quick_pay = fields.Boolean('Quick Pay Button', default=True)
    quick_pay_method = fields.Many2one('pos.payment.method', 'Quick Pay Method', default=lambda self: self.env['pos.payment.method'].search([], limit=1))
    config_color = fields.Char(string="Color")
    show_product_image = fields.Boolean(string="Show Product Image", default=True)
    configurable_color = fields.Boolean(string="Configurable Color", default=True)
    empty_order = fields.Boolean(string="Clear Orderlines", default=True)
    icon_display_type = fields.Selection([('icon', 'Icon'),('control_button', 'Control Button'),], 'Pharmacy Order Options', default="icon", required=True)
    show_is_prescription = fields.Boolean(string="Show Is Prescription", default=True)
    pos_auto_transfer_enabled = fields.Boolean(
        string="Auto transferencia de efectivo"
    )
    pos_fixed_opening_amount = fields.Monetary(
        string="Monto fijo de apertura (Gs)",
        currency_field="company_currency_id",
        default=500000
    )
    pos_transfer_threshold = fields.Monetary(
        string="Umbral de efectivo (Gs)",
        currency_field="company_currency_id",
        default=500000,
        help="Si el efectivo del día supera este monto, se transfiere el excedente."
    )
    pos_transfer_origin_journal_id = fields.Many2one(
        "account.journal", string="Diario origen (Caja)",
        domain=[("type", "=", "cash")]
    )
    pos_transfer_dest_journal_id = fields.Many2one(
        "account.journal", string="Diario destino (Banco)",
        domain=[("type", "in", ["bank"])]
    )
    company_currency_id = fields.Many2one(
        "res.currency", related="company_id.currency_id", readonly=True
    )
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    add_menu_bar = fields.Boolean(related='pos_config_id.add_menu_bar', readonly=False)
    advance_search = fields.Boolean(related='pos_config_id.advance_search', readonly=False)
    product_display_type = fields.Selection(related='pos_config_id.product_display_type', readonly=False, required=True)
    show_medicine_information = fields.Boolean(related='pos_config_id.show_medicine_information', readonly=False)
    show_details_in_products = fields.Boolean(related='pos_config_id.show_details_in_products', readonly=False)
    manufacturer = fields.Boolean(related='pos_config_id.manufacturer', readonly=False)
    storage = fields.Boolean(related='pos_config_id.storage', readonly=False)
    usage = fields.Boolean(related='pos_config_id.usage', readonly=False)
    salt_alternate = fields.Boolean(related='pos_config_id.salt_alternate', readonly=False)
    salt_composition = fields.Boolean(related='pos_config_id.salt_composition', readonly=False)
    substitute = fields.Boolean(related='pos_config_id.substitute', readonly=False)
    side_effects = fields.Boolean(related='pos_config_id.side_effects', readonly=False)
    safety_advice = fields.Boolean(related='pos_config_id.safety_advice', readonly=False)
    basic_salt = fields.Boolean(related='pos_config_id.basic_salt', readonly=False)
    quick_pay_method = fields.Many2one('pos.payment.method', related='pos_config_id.quick_pay_method', readonly=False)
    delete_order = fields.Boolean(related='pos_config_id.delete_order', readonly=False)
    quick_pay = fields.Boolean(related='pos_config_id.quick_pay', readonly=False)
    config_color = fields.Char(related='pos_config_id.config_color', readonly=False)
    show_product_image = fields.Boolean(related='pos_config_id.show_product_image', readonly=False)
    configurable_color = fields.Boolean(related='pos_config_id.configurable_color', readonly=False)
    empty_order = fields.Boolean(related='pos_config_id.empty_order', readonly=False)
    icon_display_type = fields.Selection(related='pos_config_id.icon_display_type', readonly=False, required=True)
    show_is_prescription = fields.Boolean(related='pos_config_id.show_is_prescription', readonly=False, required=True)
