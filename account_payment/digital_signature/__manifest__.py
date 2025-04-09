# -*- coding: utf-8 -*-
{
    'name': 'Firma Digital',
    'summary': """
        """,
    'description': """ Este módulo permite a las empresas gestionar y almacenar firmas digitales dentro de Odoo.""",
    'author': 'SATI',
    'website': 'https://sati.com.py/',
    'depends': ['purchase', 'stock', 'account', 'base', 'account_cobros_py'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/res_company_form.xml',
        'views/account_recibo_templates.xml'
        ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install ': False,
    'application': False,
}
