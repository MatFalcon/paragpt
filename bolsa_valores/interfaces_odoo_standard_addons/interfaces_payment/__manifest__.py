# -*- coding: utf-8 -*-
{
    'name': "Datos de Pago",

    'summary': """
        Datos de Pago
        """,

    'description': """
        Datos de Pago
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '2023.4.10.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'interfaces_tools'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/account_payment.xml',
        'views/account_payment_register.xml',
        'report/report_orden_pago.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
