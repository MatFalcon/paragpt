# -*- coding: utf-8 -*-
{
    'name': "pos_paraguay",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "RapidSoft S.A.",
    'license': 'LGPL-3',
    'website': "http://www.rapidsoft.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['point_of_sale','base', 'paraguay_backoffice'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/pos_config_view.xml',
        'report/ticket_pos.xml',
        'report/report_point_sale.xml',
        'report/config_report.xml',
        # 'template/import.xml',
        'report/caja_report.xml',

    ],
    'qweb': [
            'static/src/apps/ticket_cambio/ticket_cambio_template.xml',
        ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_paraguay/static/src/**/*',
            'pos_paraguay/static/src/apps/ticket_cambio/ticket_cambio_template.js',
        ],

    },
    'license': 'LGPL-3',


}
