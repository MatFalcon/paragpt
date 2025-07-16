# -*- coding: utf-8 -*-
{
    'name': "account_cobros_py",

    'summary': """
        Modulo de Cobros Paraguay
        """,

    'description': """
        Modulo de Cobros Paraguay
    """,

    'author': "RapidSoft S.A.",
    'website': "http://www.rapidsoft.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account','account_check','paraguay_backoffice','caja_chica','account_payment_py'],

    # always loaded
    'data': [
        'security/sale_security.xml',
        'security/ir.model.access.csv',
        'views/account_check_view.xml',
        'views/payment_view.xml',
        'views/account_move_view.xml',
        'wizard/wizard_recibo.xml',
        'views/recibo_view.xml',
        'views/menus.xml',
        'views/users_view.xml',
        'views/account_journal.xml',
        'reports/account_cobros_config.xml',
        'reports/report_cobranzas.xml',
        'views/cajas_view.xml',
        'wizard/wizard_diferencia_recibo.xml',
        'wizard/wizard_reporte_cobranzas.xml',
        'wizard/wizard_asignacion_factura.xml',
        'reports/report_cobranzas.xml',
        'reports/account_cobros_config.xml',
        'reports/report_caja_cobros.xml',
        'reports/template_recibo.xml',
        'reports/template_recibo_comun.xml',

    ],

'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}

