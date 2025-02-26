# -*- coding: utf-8 -*-
{
    'name': "Paraguay - Reportes Financieros",

    'summary': """
        Agrega los reportes contables de la Resolución General de la SET 49/14""",

    'description': """
        Agrega los reportes contables de la Resolución General de la SET 49/14
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",
    'icon':'/base/static/img/country_flags/py.png',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Localizations/Reporting',
    'version': '2023.01.15.03',
    "license": "OEEL-1",

    # any module necessary for this one to work correctly
    'depends': ['l10n_py','account_reports'],

    # always loaded
    'data': [
        'data/account_financial_html_report_data.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
