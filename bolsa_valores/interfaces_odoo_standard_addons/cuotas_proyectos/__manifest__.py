# -*- coding: utf-8 -*-
{
    'name': "Hitos de proyectos en cuotas",

    'summary': """
        Hitos de proyectos en cuotas""",

    'description': """
        Hitos de proyectos en cuotas    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Project',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','cuotas','sale_project'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/cuotas.xml',
        'views/sale.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
