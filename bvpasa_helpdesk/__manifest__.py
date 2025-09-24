# -*- coding: utf-8 -*-
{
    'name': "Helpdesk BVPASA",

    'summary': """
        Adecuaciones Helpdesk BVPASA""",

    'description': """
        Adecuaciones Helpdesk BVPASA
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Helpdesk',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','derivacion_tickets'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/ticket.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
