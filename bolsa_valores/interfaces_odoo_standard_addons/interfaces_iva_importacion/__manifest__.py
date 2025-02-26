# -*- coding: utf-8 -*-
{
    'name': "interfaces_iva_importacion",

    'summary': """
        IVA en las importaciones
    """,

    'description': """
        IVA en las importaciones
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '2023.7.25.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'resolucion_90', 'reporte_compraventa'],

    # always loaded
    'data': [
        'views/res_partner.xml',
        'views/account_account.xml',
        'views/account_move.xml',
    ],
}
