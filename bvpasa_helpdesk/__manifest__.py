# -*- coding: utf-8 -*-
{
    'name': "Helpdesk BVPASA",
    'summary': "Adecuaciones Helpdesk BVPASA",
    'description': """
        Adecuaciones Helpdesk BVPASA
    """,
    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",
    'category': 'Helpdesk',
    'version': '17.0.1.0',  # Usando formato válido con cuatro componentes
    'depends': ['base', 'helpdesk'],
    'data': [
        'data/data.xml',
        'views/ticket.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
