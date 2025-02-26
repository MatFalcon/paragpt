# -*- coding: utf-8 -*-
{
    'name': "Ingresos Diferidos",

    'summary': """
        Modificaciones al calculo de Ingresos Diferidos""",

    'description': """
        Modificaciones al calculo de Ingresos Diferidos
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '2023.08.22',

    # any module necessary for this one to work correctly
    'depends': ['base','account_asset'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/account_asset.xml',
        'views/calificacion_riesgo.xml',
        'views/instrumento.xml',
        'views/interes_grupo.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
