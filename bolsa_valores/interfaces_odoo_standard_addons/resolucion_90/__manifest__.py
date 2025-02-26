# -*- coding: utf-8 -*-
{
    'name': "Resolucion 90",

    'summary': """
        Resolución 90 - SET
        """,

    'description': """
        Resolución 90 - SET
    """,

    'author': "Interfaces S.A., Edgar Páez, Cristhian Cáceres",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '2024.1.23.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'proveedores_timbrado'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/wizard.xml',
        'views/res_company.xml',
        'views/account_move.xml',
        'views/account_journal.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
