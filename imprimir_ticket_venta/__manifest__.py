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
            'pos_invoice_ticket/static/src/js/account_ticket.js',
            'pos_invoice_ticket/static/src/xml/account_ticket_template.xml',
        ],
    },
    'installable': True,
    'application': False,
}
