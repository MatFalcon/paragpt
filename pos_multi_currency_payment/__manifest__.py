# -*- coding: utf-8 -*-
{
    'name': 'POS Multi Currency Payment',
    'live_test_url': 'http://posodoo.com/web/signup',
    'version': '1.3',
    'category': 'Point of Sale',
    'sequence': 0,
    'author': 'TL Technology',
    'website': 'http://posodoo.com',
    'price': '50',
    'description': 'Allow customers can payment with multi currency',
    "currency": 'EUR',
    'depends': ['point_of_sale','paraguay_backoffice'],
    'data': [
        'template/import.xml',
        'views/pos_config.xml',
        'views/pos_order.xml',
        'views/res_currency.xml',
        'views/account_journal.xml'
    ],
    'application': True,
    'images': ['static/description/icon.png'],
    'qweb': [
        'static/src/xml/*.xml'
    ],
    'support': 'thanhchatvn@gmail.com',
    "license": "OPL-1",
}
