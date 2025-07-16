# -*- coding: utf-8 -*-
{
    'name': "account_anticipos",

    'summary': """
        Modulo para visualización de saldos de anticipos de clientes y proveedores""",

    'author': "RapidSoft S.A.",
    'website': "http://www.rapidsoft.com.py",

    # Categories can be used to filter modules in modules listingse editaaaaa
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_check','account_payment_py','account_cobros_py'],

    # always loaded
    'data': [
        'views/account_journal_view.xml',
        'views/payment_view.xml',
    ],
    'license': 'LGPL-3',
}
