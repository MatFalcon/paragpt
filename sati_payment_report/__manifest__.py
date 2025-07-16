# -*- coding: utf-8 -*-

{
'name': 'SATI Reporte de pagos y cobros',
'version': '17.0',
'category': 'Update',
'description': """Módulo para generación de reporte PDF y EXCEL para cobranza y pago
""",
'author': 'SATI',
'website': 'http://www.sati.com.py',
'depends': ['base','account','paraguay_backoffice'],
'data': [
        'report/payment_report.xml',
        'report/config.xml',
        'wizard/wizard_payment_view.xml',
        'security/ir.model.access.csv',
        ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
