# -*- coding: utf-8 -*-
{
    'name': "Conciliación Automática",

    'summary': """
        Se agrega botón para hacer conciliaciones bancarias automáticas en los extractos bancarios no coinciliados""",

    'description': """
        Se agrega botón para hacer conciliaciones bancarias automáticas en los extractos bancarios no coinciliados
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Payment',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/account_bank_statement.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
