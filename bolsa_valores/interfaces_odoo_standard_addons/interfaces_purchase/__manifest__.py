# -*- coding: utf-8 -*-
{
    'name': "interfaces_purchase",

    'summary': """
        Modulo estandar para compras
    """,

    'description': """
        Modulo estandar para compras
         - Agrega reporte de costeos en pedidos de compras
    """,

    'author': "Interfaces S.A., Johann Bronstrup Mohr",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Inventory/Purchase',
    'version': '2023.06.28.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'purchase', 'stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'report/report_costo_importacion.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/purchase.xml',
        'views/stock_picking.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
