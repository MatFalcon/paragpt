{
    'name': "BVA PBP",

    'summary': """
        Genera facturas con datos importados del PBP.
        """,

    'description': """
        Genera facturas con datos importados del PBP.
    """,

    'author': "SATI",
    'website': "http://www.sati.com.py",
    'category': 'PBP',
    'version': '17.0.0.0',
    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale_management', 'product','mail','account_voucher', 'paraguay_backoffice', 'bva_custom'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/account_voucher.xml',
        'views/liquidaciones_view.xml',
        'views/resoluciones_view.xml',
        'views/custodia_emisiones_view.xml',
        'views/product_view.xml',
        'views/configuraciones_view.xml',
        'views/vencimiento_intereses_view.xml',
        'views/sincronizacion_logs_view.xml',
        'views/vencimiento_cartera_view.xml',
        'views/account_move_view.xml',
        'views/gastos_adm_view.xml',
        'views/transferencia_cartera_view.xml',
        'views/cartera_inversiones_view.xml',
        'views/negociaciones_view.xml',
        'views/operacion_futuro_view.xml',
        'views/sistema_tradicional_view.xml',
        'views/reporto.xml',
        'wizard/wizard_volumen_negociado.xml',
        'wizard/wizard_facturacion_mensual.xml',
        'views/menus.xml',
        'reports/report_volumen_negociado.xml'
    ],

}
# -*- coding: utf-8 -*-
