{
    'name': 'POS Invoice Ticket',
    'version': '1.0',
    'summary': 'Permite imprimir tickets desde facturas vinculadas a ventas del POS',
    'author': 'Tu Nombre',
    'license': 'LGPL-3',
    'category': 'Accounting',
    'depends': ['point_of_sale', 'account'],
    'data': [
        'views/account_move_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'imprimir_ticket_venta/static/src/js/account_ticket.js',
            'imprimir_ticket_venta/static/src/xml/account_ticket_template.xml',
        ],
        'point_of_sale.assets': [
            'imprimir_ticket_venta/static/src/js/account_ticket.js',
        ],
    },

    'installable': True,
    'application': False,
}
