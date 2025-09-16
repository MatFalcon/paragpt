# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "POS Pharmacy Management",
  "summary"              :  """Odoo POS Pharmacy Management is the complete solution for all your pharmacy needs. It allows you to manage every pharmacy operation with ease and efficiency. The module enables you to add medicines, doctors, salts, chemical classes, diseases, and much more. Also, the Odoo app offers a brand new and improved interface with icons, advanced search, and navigation tools for a more refined user experience. medical store management|medicine sale in odoo, pharmacy|medicine store, medical store|medicine store in odoo|POS Drug Management|Pharmacy Billing System|POS Medicine|POS for Pharmacists|POS For Healthcare and medicine
""",
  "category"             :  "Point Of Sale",
  "version"              :  "1.0.3",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/odoo-pos-pharmacy-management.html",
  "description"          :  """POS Pharmacy Management solves all your medical shop requirements with a single solution. It makes operating and managing efficient and hassle-free.
                              odoo pos pharmacy management, 
                              pos pharmacy management, 
                              manage pharmacy in odoo, 
                              drug store management, 
                              odoo, odoo pos, odoo app, odoo admin, odoo apps, 
                              medical store management, 
                              medicine sale in odoo, pharmacy, 
                              medicine store, medical store, 
                              medicine store in odoo, 
                              medical store in odoo, 
                              point of sale, 
                              odoo point of sale, 
  """,
  "live_test_url"        :  "https://odoodemo.webkul.com/?module=pos_pharmacy_management&custom_url=/pos/auto",
  "depends"              :  ['point_of_sale'],
  "data"                 :  [
                              'security/ir.model.access.csv',
                              'views/inherit_pos_order.xml',
                              'views/inherit_product_product_view.xml',
                              'views/inherit_uom_category_view.xml',
                              'views/inherit_res_config_settings.xml',
                              'views/inherit_res_partner.xml',
                              'views/actions.xml',
                              'views/menus.xml' ,
                              'views/pharmacy_view.xml',
                              'views/pos_config.xml'
                            ],
  "demo"                 :  [
                              'demo/models.xml',
                              'demo/products.xml',
                            ],
  "assets"               :  {
                              'point_of_sale._assets_pos': [ '/pos_pharmacy_management/static/src/**/*',
                                      'pos_pharmacy_management/static/src/css/location_lot_popup.css',
                                      'pos_pharmacy_management/static/src/app/popup/location_lot_selection_popup/location_lot_selection_popup.js',
                                      'pos_pharmacy_management/static/src/app/popup/location_lot_selection_popup/location_lot_selection_popup.xml',
                                      'pos_pharmacy_management/static/src/app/popup/uom_location_selection_popup/uom_location_selection_popup.xml',
                                      'pos_pharmacy_management/static/src/app/popup/uom_location_selection_popup/uom_location_selection_popup.js',
         ],
			                      },
  "images"               :  ['static/description/Banner.gif'],
  "application"          :  True,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  199,
  "currency"             :  "USD",
  "pre_init_hook"        :  "pre_init_check",
}
