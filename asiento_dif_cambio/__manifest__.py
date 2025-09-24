# -*- coding: utf-8 -*-
{
    'name': "Asiento por diferencia de Cambio",

    'summary': """
        Modulo que crea asiento por diferencia de cambio""",

    'description': """
        Modulo que crea asiento por diferencia de cambio
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/res_config_settings.xml',
        'views/templates.xml',
        'views/wizard.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
