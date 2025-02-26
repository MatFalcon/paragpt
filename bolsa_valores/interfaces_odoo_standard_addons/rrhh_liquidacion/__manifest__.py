# -*- coding: utf-8 -*-
{
    'name': "Liquidación de salarios",

    'summary': """
Módulo para LIQUIDACIÓN DE SALARIOS""",

    'description': """
Módulo para LIQUIDACIÓN DE SALARIOS
""",

    'author': "Interfaces S.A., Cristhian Cáceres",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources/Payroll',
    'version': '2024.2.14.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_contract', 'rrhh_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/estructura_despido.xml',
        'data/estructura_renuncia.xml',
        'data/estructura_jubilacion.xml',
        'views/res_config_settings.xml',
        'views/hr_payslip.xml',
        'views/wizard_calculo_despido.xml',
        'views/wizard_calculo_renuncia.xml',
        # 'views/wizard_calculo_jubilacion.xml',
        'report/hr_payslip_recibo.xml',
    ],
}
