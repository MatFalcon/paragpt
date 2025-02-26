# -*- coding: utf-8 -*-
{
    'name': "Plantillas de Contrato",

    'summary': """
        Modulo que agrega las plantillas de Contratos""",

    'description': """
        Modulo que agrega las plantillas de Contratos
    """,

    'author': "Interfaces S.A",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'HR',
    'version': '2024.1.23.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'reportes_ministerio_trabajo_py'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract.xml',
        'views/plantillas_contrato.xml',
        'views/plantillas_contrato_subseccion.xml',
        'views/res_company.xml',
        # 'views/hr_employee.xml',
        'report/hr_contract_report.xml',
    ],
}
