# -*- coding: utf-8 -*-
{
    'name': "Creación de recepción para notas de crédito",

    'summary': """
        Creación de recepción para notas de crédito
        """,

    'description': """
        Creación de recepción para notas de crédito
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '2023.8.3.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock_account', 'interfaces_timbrado'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/res_config_settings.xml',
        'views/account_invoice.xml',
        'views/stock_picking_type.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
