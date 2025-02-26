# -*- coding: utf-8 -*-
{
    'name': "Interfaces Timbrado",

    'summary': """
        Módulo de timbrado - Interfaces S.A.
        """,

    'description': """
        Módulo de timbrado - Interfaces S.A.
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '1.2023.7.7.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'standard_ruc'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/timbrado.xml',
        'views/account_journal.xml',
        'views/account_move.xml',

        # 'views/account_invoice.xml',
        # 'views/actualiza_nro_wizard.xml',
        # 'views/split_factura.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
