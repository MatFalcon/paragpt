# -*- coding: utf-8 -*-
{
    'name': "Transferencias",

    'summary': """
       Transferencias""",

    'description': """
        Modulo que agrega las transferencias
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '2023.3.27.1',

    # any module necessary for this one to work correctly
    'depends': ['base','interfaces_payment'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/account_journal.xml',
        'views/account_payment.xml',
        'views/account_transferencia.xml',
        'views/report_account_payment_transfer.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
