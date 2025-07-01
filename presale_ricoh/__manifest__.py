# -*- coding: utf-8 -*-
{
    'name': 'Presale Ricoh',
    'version': '1.0',
    'category': 'Sales/CRM',
    'summary': 'Módulo para la gestión de preventas integrado con CRM y Ventas',
    'description': """
    Este módulo proporciona funcionalidades para la gestión de proyectos de preventas, integrado con los procesos de CRM y Ventas.
    """,
    'author': 'SATI',
    'website': 'http://www.sati.com.py',
    'depends': ['base', 'crm', 'sale', "presale", "stock",'crm_ricoh', 'operating_unit'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/sequence.xml',
        'data/presale_config_data.xml',
        'views/crm_lead_view.xml',
        'views/presale_order_views.xml',
        'views/presale_order_item_view.xml',
        'views/presale_order_item_detail.xml',
        'views/product_template_view.xml',
        'views/presale_menu.xml',
        'views/crm_analisis_credito.xml',
        'views/presale_config_views.xml',
        'views/sale_order_views.xml',
        'views/stock_production_lot_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
