# -*- coding: utf-8 -*-
{
'name': 'Impresion De Tickets Desde La venta',
'version': '1.0',
'category': 'Update',
'description': """Imprime los ticket hechos en el punto de ventas desde el modulo de ventas
""",
'author': 'Sati',
'website': 'http://www.sati.com.py',
'depends': ['point_of_sale'],
'data': [
            'views/sale_order.xml',
            'report/sale_ticket_report.xml',
            'report/sale_ticket_template.xml',
],
'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',

    'assets': {
        'web.assets_backend': [
            'imprimir_ticket_venta/static/src/js/sale_ticket.js',
            'imprimir_ticket_venta/static/src/xml/sale_ticket.xml',
        ],
    },
}

