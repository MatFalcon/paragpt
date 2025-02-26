# -*- coding: utf-8 -*-
{
    'name': "Autorizacion timbrado",

    'summary': """
        Se agrega los campos para autorizacion de timbrado""",

    'description': """Se agrega los campos para autorizacion de timbrado
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Invoicing',
    'version': '2021.08.05',

    # any module necessary for this one to work correctly
    'depends': ['base','interfaces_timbrado'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/autorizacion_timbrado.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
