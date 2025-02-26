# -*- coding: utf-8 -*-
{
    'name': "PBP Novedades",

    'summary': """
        Genera facturas con datos importados del PBP.
        """,

    'description': """
        Genera facturas con datos importados del PBP.
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'PBP',
    'version': '2024.30.01.01',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'sale_management', 'product','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/fondo_garantias.xml',
        'views/gastos_administrativos.xml',
        'views/inversion_fondo_garantias.xml',
        'views/liquidaciones.xml',
        'views/transferencia_cartera.xml',
        'views/wizard.xml',
        'views/templates.xml',
        'views/account.xml',
        # 'views/account_move.xml',
        # 'views/res_partner.xml',
        'views/product.xml',
        'views/cartera_inversion.xml',
        'views/res_config_settings.xml',
        'views/reporto.xml',
        'views/control_pagos.xml',
        'views/compensacion.xml',
        'views/tcero.xml',
        'views/exportar_liquidaciones.xml',
        'views/wizard_volumen_negociado.xml',
        'views/sincronizacion_logs.xml',
        'views/operacion_futuro.xml',
        'views/account_journal.xml',
        'views/wizard_sudameris.xml',
        'views/res_company.xml',
        'views/resoluciones_view.xml',
        'views/configuraciones.xml',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],

    'assets': {
        'web.assets_common': [
            'pbp/static/src/css/styles.css',
        ]
    },
}
