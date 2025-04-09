# -*- coding: utf-8 -*-
{
'name': 'Account Internal Transfers',
'version': '17.0',
'category': 'Update',
'description': """Module for administration of internal transfers between Journals.
""",
'author': 'Rapidsoft',
'website': 'http://www.rapidsoft.com.py',
'depends': ['account','account_check'],
'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/internal_transfer_view.xml',
        'reports/config.xml',
        'reports/internal_transfer_report.xml',
        'reports/efectivizacion_report.xml',
      ],
'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
