# -*- coding: utf-8 -*-
{
    'name': "bvpasa_account",

    'summary': """
        Módulo para personalización de account en BVPASA
    """,

    'description': """
        Módulo para personalización de account en BVPASA
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','resolucion_90','account_followup'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/product.xml',
        'views/account_bank_statement.xml',
        #'views/account_move.xml',
        'views/account_account.xml',
        'views/account_report_view.xml',
        'views/report_financial.xml',
        'views/res_partner_bank.xml',
        'views/wizard_cuentas_bancarias.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
