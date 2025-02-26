# -*- coding: utf-8 -*-
{
    'name': "Notas de remision",

    'summary': """
        Notas de remision""",

    'description': """
        Notas de remision
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Stock',
    'version': '2022.02.20.01',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'interfaces_timbrado','sale_stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/stock_picking.xml',
        'views/report_nota_remision.xml',
        'views/account_journal.xml',
        'views/stock_picking_type.xml',
    ],
}
