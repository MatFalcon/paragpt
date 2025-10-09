{
    'name': 'Ventas  Credito Punto de Ventas',
    'version': '17.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'Habilita ventas a crédito en el Punto de Venta con selección de plazos',
    'description': """
        Módulo de Ventas a Crédito para POS
        ===================================
        
        Este módulo permite:
        * Configurar ventas a crédito en el POS
        * Seleccionar términos de pago durante la venta
        * Aplicar automáticamente el método de pago "Cuenta de Cliente"
        * Generar facturas con términos de pago apropiados
        * Validar límites de crédito de clientes
    """,
    'author': 'SATI',
    'website': 'https://sati.com.py',
    'license': 'LGPL-3',
    'depends': [
        'point_of_sale',
        'account',
        'pos_online_payment',
    ],
    'data': [
        'security/ir.model.access.csv',
        # 'data/pos_payment_method_data.xml',
        'views/pos_config_views.xml',
        'views/pos_order_views.xml',
        # 'views/account_payment_term_views.xml',
        'wizard/pos_credit_config_wizard_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_credit_sales/static/src/**/*'
        ],
    },

        # 'assets': {
        # 'point_of_sale.assets_pos': [
        #     'pos_credit_sales/static/src/js/models.js',
        #     'pos_credit_sales/static/src/js/pos_store.js', 
        #     'pos_credit_sales/static/src/js/payment_term_popup.js',
        #     'pos_credit_sales/static/src/js/payment_screen.js',
        #     'pos_credit_sales/static/src/xml/payment_term_popup.xml',
        #     'pos_credit_sales/static/src/xml/pos.xml',
        # ],
    'demo': [
        'demo/pos_config_demo.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}