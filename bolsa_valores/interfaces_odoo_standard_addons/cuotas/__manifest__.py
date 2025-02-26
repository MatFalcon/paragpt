# -*- coding: utf-8 -*-
{
    'name': "Cuotas",

    'summary': """
        Cuotas
        """,

    'description': """
        Cuotas
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Base',
    'version': '2022.10.24.01',

    # any module necessary for this one to work correctly
    'depends': ['base','contacts','account_accountant','portal','utm',],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/cuotas.xml',
        'views/res_partner.xml',
        'views/wizard_facturar.xml',
        # 'views/cuotas_portal_template.xml',
        #'views/product.xml',
        'views/account_move.xml',
        'views/wizard_generar_cuota.xml',
        #'views/wizard_whatsapp.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
   
}
