# -*- coding: utf-8 -*-
{
    'name': "Integracion de Notas de remision en Facturacion con Inventario",

    'summary': """
    Integracion de Notas de remision en Facturacion con Inventario
        """,

    'description': """
        Relaciona las notas de remision que están en facturacion con 
        el módulo de Inventario.
        Permite cargar productos desde un Envío de inventario a la Remision
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','notas_remision_account','stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/notas_remision.xml',
        'views/stock_picking.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
