# -*- coding: utf-8 -*-
{
    'name': "Paraguay - Accounting",

    'summary': """
        Contabilidad - Paraguay
        """,

    'description': """
        Agrega plan contable sugerida por la SET.
        Agrega grupos de cuentas sugeridos por la SET.
        Agrega impuestos IVA Exentas, 10%, 5% para ventas y compras.
        Establece las cuentas por cobrar por pagar, banco, efectivo, transferencias y por cobrar POS.
        Establece la configuración de impuestos incluidos en los totales de facturas.
        Establece 0 decimales para la moneda PYG.
    """,

    'author': "Interfaces S.A.",
    'website': "http://www.interfaces.com.py",
    'icon': '/base/static/img/country_flags/py.png',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Accounting/Localizations/Account Charts',
    "license": "LGPL-3",
    'version': '2023.1.18.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'data/account_chart_template_data.xml',
        'data/account.account.tag.csv',
        'data/account.account.template.csv',
        'data/account.group.template.csv',
        'data/account_tax_group_data.xml',
        'data/account_tax_template_data.xml',
        'data/account_chart_post_data.xml',
        'data/res_currency.xml',
        'views/views.xml',
        'views/templates.xml',
        'data/menu_item.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'post_init_hook': 'post_init_hook',
}
