# -*- coding: utf-8 -*-
{
    'name': "Integración con Bancard",

    'summary': """
        Integración de Reportes Automáticos de Bancard""",

    'description': """
        Integración de Reportes Automáticos de Bancard
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/integracion_bancard.xml',
        'views/integracion_campus.xml',
        'views/cursos.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
