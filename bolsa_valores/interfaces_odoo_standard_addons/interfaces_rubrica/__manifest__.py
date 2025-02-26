# -*- coding: utf-8 -*-
{
    'name': "Libros rubricados",

    'summary': """
        Modulo para registro de rúbricas
    """,

    'description': """
        Modulo para registro de rúbricas
        -Se pone el campo de imagen en rubricas como no campo no requerido
        -Se modifica campo en la generacion del reporte de compras y ventas para que llame el campo ref y no el campo name.
        -Se agrega validacion si es que el libro a generar tiene o no adjuntado la imagen para que no llame en el reporte en el
        caso de que no tenga.
        -Se agregar libro mayor en rubricas
    """,

    'author': "Interfaces S.A. Johann Bronstrup, Edgar Gonzalez, Cristhian Cáceres",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Account',
    'version': '2024.2.1.2',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'account_reports', 'interfaces_timbrado'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/registro_rubrica.xml',
        'views/informe_rubrica.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/res_config_settings.xml',
    ],
}
