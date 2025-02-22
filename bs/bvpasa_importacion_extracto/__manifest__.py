# -*- coding: utf-8 -*-
{
    'name': "Importacion de Extracto de Cuenta",

    'summary': """
        Modulo que agrega la opcion de importar las lineas de extracto bancario""",

    'description': """
        Modulo que agrega la opcion de importar las lineas de extracto bancario
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
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/account_bank_statement.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
