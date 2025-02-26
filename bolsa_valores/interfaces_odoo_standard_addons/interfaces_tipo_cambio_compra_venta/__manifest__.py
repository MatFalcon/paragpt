# -*- coding: utf-8 -*-
{
    'name': "interfaces_tipo_cambio_compra_venta",

    'summary': """
        Tipos de cambio de Compra y Venta en las monedas""",

    'description': """
        Tipos de cambio de Compra y Venta en las monedas""",

    'author': "Interfaces S.A., Cristhian Cáceres",
    'website': "https://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '2024.2.6.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account_accountant', 'sale'],

    # always loaded
    'data': [
        'views/res_currency.xml',
        'views/account_move.xml',
        'views/account_payment.xml',
        'views/account_payment_register.xml',
    ],
}
