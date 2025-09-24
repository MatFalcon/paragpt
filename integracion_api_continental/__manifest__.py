# -*- coding: utf-8 -*-
{
    'name': "integracion_api_continental",

    'summary': """
        Integración con el módulo apicontinental""",

    'description': """
        Integración con el módulo apicontinental, para la integración con el API del Banco Continental
    """,

    'author': "Interfaces S.A., Gustavo Bazan",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'apicontinental', 'account', 'interfaces_payment'],

    # always loaded
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/res_users.xml',
        'views/res_company.xml',
        'views/account_journal.xml',
        'views/account_bank_statement.xml',
        'views/account_payment.xml',
        'views/res_partner.xml',
    ],
}
