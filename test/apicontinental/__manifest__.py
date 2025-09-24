# -*- coding: utf-8 -*-
{
    'name': "apicontinental",

    'summary': """Integración al API del Banco Continental""",

    'description': """
        Integración al API del Banco Continental
    """,

    'author': "Interfaces S.A., Gustavo Bazan",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/listados.xml'
    ],
}
