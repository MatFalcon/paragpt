# -*- coding: utf-8 -*-
{
    'name': "Reporte REI para el IPS",

    'summary': """
        Reporte en fomrato REI para el IPS - Paraguay""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Interfaces S.A., Cristhian Cáceres",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources/Payroll',
    'version': '2023.12.28.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'report_xlsx', 'rrhh_payroll'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'data/data.xml',
        'views/templates.xml',
    ],
}
