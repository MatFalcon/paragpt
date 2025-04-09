# -*- coding: utf-8 -*-
{
    'name': "account_orden_pago_py",

    'summary': """
        Modulo a medida de Ordenes de Pago""",

    'description': """
        Modulo a medida de Ordenes de Pago 
    """,

    'author': "RapidSoft S.A.",
    'website': "http://www.rapidsoft.com.py",

    # Categories can be used to filter modules in modules listingse editaaaaa
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_check'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/account_move_view.xml',
        'views/orden_pago_views.xml',
        'views/account_journal_view.xml',
        'views/payment_view.xml',
        'sequence/orden_pago_sequence.xml',
        'wizard/anulacion_orden_pago.xml',
        'reports/config_reports_payment_py.xml',
        'reports/report_payment_py.xml',
        'reports/payment_reporte.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'wizard/wizard_diferencia_op.xml',
        'wizard/wizard_asignacion_factura.xml',

    ],
    'license': 'LGPL-3',
}
