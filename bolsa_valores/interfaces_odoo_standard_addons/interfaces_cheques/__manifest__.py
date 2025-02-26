# -*- coding: utf-8 -*-
{
    'name': "Gestión de cheques",

    'summary': """
        Gestión de cheques""",

    'description': """
        Agrega tipo de cheque de Terceros o propios a los Pagos.
        Agrega estado de cheques a los pagos.
        Permite gestionar el rechazo de cheques.
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','interfaces_payment','interfaces_transferencias'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/account_payment.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
