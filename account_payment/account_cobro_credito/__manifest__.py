# -*- coding: utf-8 -*-
{
    'name': "account_cobro_credito",

    'summary': """
        Modulo para hacer obligatorio carga de recibos en facturas credito Paraguay
        """,

    'author': "SATI",
    'website': "http://www.sati.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','paraguay_backoffice','account_cobros_py'],

    # always loaded
    'data': [
        'views/users_view.xml',
    ],

'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}

