# -*- coding: utf-8 -*-
{
    'name': "Derivacion de tickets",

    'summary': """
        Derivacion de tickets""",

    'description': """
Derivacion de tickets    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Helpdesk',
    'version': '2022.07.12.01',

    # any module necessary for this one to work correctly
    'depends': ['base','helpdesk'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/views.xml',
        'views/helpdesk.xml',
        #'views/helpdesk_ticket_pivot.xml',
        'views/templates.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
