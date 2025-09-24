# -*- coding: utf-8 -*-
{
    'name': "Cuentas especificas para moneda extranjera en Contactos",

    'summary': """
        Cuentas especificas para moneda extranjera en Contactos""",

    'description': """
        Cuentas especificas para moneda extranjera en Contactos
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        #'views/res_partner.xml',
        'views/res_currency.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
