# -*- coding: utf-8 -*-
{
    'name': "Recibo de Cobranza OfficeDesign",
    'author': "My Company",
    'website': "https://www.yourcompany.com",
    'category': 'Uncategorized',
    'version': '17.0.1.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account_cobros_py'],
    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'reports/report.xml',
        'reports/recibo_cobranza_off.xml',
    ],
}

