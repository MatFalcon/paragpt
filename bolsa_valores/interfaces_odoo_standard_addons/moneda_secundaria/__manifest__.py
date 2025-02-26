# -*- coding: utf-8 -*-
{
    'name': "Moneda secundaria",

    'summary': """
        Moneda secundaria de la Compañia""",

    'description': """
        Permite tener una moneda secundaria en los apuntes contables.
    """,

    'author': "Interfaces S.A.",
    'website': "https://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '2023.5.16.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/res_company.xml',
        'views/account_move.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
