# -*- coding: utf-8 -*-
{
    'name': "rrhh_payroll",

    'summary': """
        Modificaciones en el comportamiento de las  nóminas
        """,

    'description': """
        Modificaciones en el comportamiento de las  nóminas
    """,

    'author': "Interfaces S.A., Cristhian Cáceres",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Human Resources/Payroll',
    'version': '2023.12.13.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'report_xlsx', 'rrhh_novedades', 'hr_holidays', 'reportes_ministerio_trabajo_py'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data.xml',
        'data/estructura_salario_hora.xml',
        'data/estructura_salario_jornal.xml',
        'data/estructura_salario_mensual.xml',
        'views/antiguedad_vacaciones.xml',
        # 'views/hr_employee.xml',
        'views/hr_contract.xml',
        'views/hr_leave.xml',
        'views/notificacion_vacacion.xml',
        'views/hr_payslip.xml',
        'views/hr_payslip_run.xml',
        'views/hr_payslip_run_report_concept.xml',
        'reports/hr_payslip.xml',
        'reports/notificacion_vacacion_comunicacion.xml',
        'reports/notificacion_vacacion_recibo.xml',
        'reports/notificacion_vacacion_usufructo.xml',
        'reports/notificacion_vacacion_full.xml',
        'reports/report_payslip_run_totales.xml',
        'reports/reporte_vacaciones.xml',
        'reports/hr_payslip_run.xml',
    ],
}
