# -*- coding: utf-8 -*-
{
    'name': "Notas de remisión en Facturacion",

    'summary': """
        Notas de remisión en Facturacion""",

    'description': """
        Documento de notas de remisión en el módulo de Facturación.
        Independiente del módulo de Stock.

    """,

    'author': "Interfaces S.A.",
    'website': "https://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '2023.08.29.1',

    # any module necessary for this one to work correctly
    'depends': ['base','interfaces_timbrado'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/notas_remision.xml',
        'views/account_journal.xml',
        'views/report_nota_remision.xml',
        'views/account_move.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
