# -*- coding: utf-8 -*-
{
    'name': "Integración Pagopar",

    'summary': """
       Integración Pagopar""",

    'description': """
        Integración Pagopar
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Payment',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account','payment','website_sale','base_address_city','dimensiones_product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/res_partner.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/payment_acquirer_templates.xml',
        'views/account_move.xml',
        'data/payment_acquirer_data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',

}