# -*- coding: utf-8 -*-
{
    'name': "mantenimiento_registro",

    'summary': """
        Parametrización de contactos y lista de precios para mantenimiento
        """,

    'description': """
        Parametrización de contactos y lista de precios para mantenimiento
    """,

    'author': "Interfaces, Gustavo Bazan",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'account_accountant'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mantenimiento_registro.xml',
        'views/res_partner.xml',
        'views/product.xml',
        'views/account_move.xml'
    ],
}
