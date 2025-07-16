# -*- coding: utf-8 -*-
{
'name': 'Descuento de Cheques',
'version': '17.0',
'category': 'Update',
'description': """Modulo de descuento de cheques
""",
'author': 'Rapidsoft',
'website': 'http://www.rapidsoft.com.py',
'depends': ['account_check','account'],
'data': [
        'security/ir.model.access.csv',
        'views/cheques_descuento.xml',
        'data/descuento.xml',
        'security/discount_security.xml',
      ],
'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
