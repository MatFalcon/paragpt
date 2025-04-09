# -*- coding: utf-8 -*-
{
'name': 'Account Deposit on bank account',
'version': '17.0',
'category': 'Update',
'description': """Module for administration and deposit of cash/check/others to a bank account.
This module depends of our fork of the account_check addon by the odoo partner ADHOC.
""",
'author': 'Rapidsoft',
'website': 'http://www.rapidsoft.com.py',
'depends': ['account_check'],
'data': [
        'security/ir.model.access.csv',
        'views/cheques_deposito.xml',
      ],
'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
