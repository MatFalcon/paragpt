# -*- coding: utf-8 -*-
{
    'name': "resolucion_90_multicurrency",

    'summary': """
        Se habilitan opciones de multimoneda para las compañias que necesiten los informes de resolución 90 en una moneda distina a la principal
        """,

    'description': """
        Se habilitan opciones de multimoneda para las compañias que necesiten los informes de resolución 90 en una moneda distina a la principal
    """,

    'author': "Interfaces S.A., Cristhian Cáceres",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '2023.6.9.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'resolucion_90'],

    # always loaded
    'data': [
        'views/resolucion_90_wizard.xml',
    ],
}
