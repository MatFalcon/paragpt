# -*- coding: utf-8 -*-
{
    'name': "Forzar igualdad de saldos en el extracto bancario",

    'summary': """
        Al publicar un extracto bancario, se comprueba si los saldos finales son iguales, para evitar crear una línea por la diferencia entre ambos
    """,

    'description': """
        Al publicar un extracto bancario, se comprueba si los saldos finales son iguales, para evitar crear una línea por la diferencia entre ambos
    """,

    'author': "Interfaces S.A., Cristhian Cáceres",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Accounting',
    'version': '1.2022.8.26.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [],
}
