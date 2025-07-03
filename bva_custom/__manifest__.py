# -*- coding: utf-8 -*-
{
    'name': "bva_custom",

    'summary': """
        Módulo de ajustes a medida BVPASA
    """,

    'description': """
        Módulo de personalizaciones BVPASA
    """,

    'author': "SATI",
    'website': "http://www.sati.com.py",

    'category': 'CUSTOM',
    'version': '17.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','paraguay_backoffice','account_followup', 'account_payment_py'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/data.xml',
        'data/grupos_orden_pago.xml',
        'data/mail_template_retenciones.xml',
        'data/mail_template_data.xml',
        'views/account_orden_pago.xml',
        'views/account_move_view.xml',
    ],

}
