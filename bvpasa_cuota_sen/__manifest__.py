# -*- coding: utf-8 -*-
{
    'name': "Cuota SEN CBSA",

    'summary': """
        Modulo que agrega reporte de Cuota SEN CBSA""",

    'description': """
         Modulo que agrega reporte de Cuota SEN CBSA
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','bvpasa_account','pbp'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/res_config_settings.xml',
        'views/account_move.xml',
        'views/res_partner.xml',
        'views/wizard.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
