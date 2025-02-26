# -*- coding: utf-8 -*-
{
    'name': "Reportes para el Ministerio de Trabajo - Paraguay",

    'summary': """
        Reportes para el Ministerio de Trabajo y la SET - Paraguay
        """,

    'description': """
        Reportes para el Ministerio de Trabajo y la SET - Paraguay
    """,

    'author': "Interfaces S.A., Cristhian Cáceres",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Human Resources/Payroll',
    'version': '2024.2.19.1',
    'external_dependencies': {
        'python': [
            'xlsxwriter',
        ],
    },
    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_attendance', 'hr_holidays', 'hr_payroll', 'report_xlsx'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'data/res_bank.xml',
        'data/estructura_aguinaldo.xml',
        'data/estructura_vacaciones.xml',
        'views/hr_contract.xml',
        'views/hr_employee.xml',
        'views/hr_leave_type.xml',
        'views/hr_payroll_structure_type.xml',
        'views/reportes_ministerio_trabajo.xml',
        'views/reportes_ministerio_trabajo_slow_mode.xml',
        'views/reporte_set.xml',
        'views/res_company.xml',
        'views/wizard_salario_minimo.xml',
        'views/calendario_feriado.xml',
        'views/res_config_settings.xml',
        # 'report/empleados_y_obreros_report.xml',
        # 'report/sueldos_y_jornales_report.xml',
        # 'report/lista_nominas_report.xml',
        'report/reportes_ministerio_trabajo.xml',
        'report/hr_contract_active_history_report.xml',
    ],
    'post_init_hook': 'reportes_ministerio_trabajo_py_post_init_hook',
}
