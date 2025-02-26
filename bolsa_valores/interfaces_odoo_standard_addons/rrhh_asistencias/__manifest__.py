# -*- coding: utf-8 -*-
{
    'name': "Modulo de asistencias - Interfaces S.A.",

    'summary': """
        Modulo de asistencias - Interfaces S.A.""",

    'description': """
        Modulo de asistencias - Interfaces S.A.
    """,

    'author': "Interfaces S.A., Cristhian Cáceres, Johann Bronstrup",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources/Payroll',
    'version': '2024.2.1.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_attendance', 'rrhh_payroll'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/hr_asistencias_security.xml',
        'data/data.xml',
        'views/hr_attendance_calendar.xml',
        'views/hr_attendance_auto_check.xml',
        'views/resource_calendar.xml',
        'views/hr_employee.xml',
        'views/hr_contract.xml',
        'views/hr_attendance.xml',
        'views/hr_payslip.xml',
        'views/marcadores.xml',
        'views/marcaciones.xml',
        'views/res_config_settings.xml',
        'views/resource_calendar_attendance.xml',
        # 'views/calendario_feriado.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            'rrhh_asistencias/static/src/xml/**/*',
        ],
    },
}
