# -*- coding: utf-8 -*-
{
    'name': "Sale invoicing terms",

    'summary': """
        Manage custom invoicing terms based upon sale order confirmation""",

    'description': """

    """,

    'author': "SATI",
    'website': "http://www.sati.com.py",


    'category': 'Uncategorized',
    'version': '0.1',

    'depends': ['base','account','sale','mail'],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/activity_type_view.xml',
        'views/sale_invoice_terms_views.xml',
        'views/sale_invoice_terms_conditions_views.xml',
        'views/res_config_settings_views.xml',
        'wizard/invoice_term_condition_wizard_view.xml',
        'data/sequence.xml'
    ],

}