{
    'name': 'Impresión De Tickets Desde La Venta',
    'version': '1.0',
    'category': 'Update',
    'description': """Imprime los ticket hechos en el punto de ventas desde el módulo de ventas""",
    'author': 'Sati',
    'website': 'http://www.sati.com.py',
    'depends': ['point_of_sale', 'pos_paraguay'],
    'data': [
        'views/sale_order.xml',
        'report/sale_ticket_report.xml',
        'report/sale_ticket_template.xml',
    ],
    'qweb': [
        'static/apps/ticket_cambio/ticket_cambio_template.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            # Importa el template y el JS del ticket de cambio

            'imprimir_ticket_venta/static/apps/ticket_cambio/ticket_cambio_template.xml',
            'imprimir_ticket_venta/static/src/js/account_ticket.js',
            'imprimir_ticket_venta/static/apps/ticket_cambio/ticket_cambio_template.js',
            # Archivos de lógica de impresión
            'imprimir_ticket_venta/static/src/js/sale_ticket.js',
            'imprimir_ticket_venta/static/src/xml/sale_ticket.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}
