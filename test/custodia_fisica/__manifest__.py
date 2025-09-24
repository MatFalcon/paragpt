# -*- coding: utf-8 -*-
{
    'name': "custodia_fisica",

    'summary': """
        Módulo para gestión de custodias físicas
    """,

    'description': """
    Módulo para gestión de custodias físicas
    Contabilidad -> Contabilidad -> Líneas de custodias físicas
        - Se utiliza la vista para importar los datos mediante archivo
        - El monto y la divisa debe ser en dolares
        - Se agrupan por mes y por cliente para generar Facturación de Custodias Físicas

    Contabilidad -> Contabilidad -> Facturación Custodias Físicas
        - Se utiliza la vista para aplicar descuentos y generar facturas a partir de los registros confirmados
        - Al momento de facturar se indica la diario y la fecha de la factura
        - La factura se genra en GS
        
    Contabilidad -> Configuración -> Aranceles por Cantidad
        - Se configura el rango de cantidad y jornales aplicados a cada uno
        - Tener en cuenta solo se debe tener un arancel activo y predeterminado
        - En caso que el cliente tenga un arancel asignado, este será usado en vez del predeterminado

    Contabilidad -> Configuración -> Aranceles por Monto
        - Se configura el rango del monto y jornales aplicados a cada uno
        - Tener en cuenta solo se debe tener  un arancel activo y predeterminado
        - En caso que el cliente tenga un arancel asignado, este será usado en vez del predeterminado

    Contabilidad -> Contabilidad -> Líneas de Custodias Importadas
        - Listado de lineas importadas des la api de green 

    Acciones programadas:
        - Obtener Líneas de Custodia API -> para conexión con la api y generar los datos en el 
            modelo de líneas importadas 

        - Procesar Custodias Importadas -> para procesar líneas importadas a líneas de custodia 
            física agrupando entidad, tipo de título y fecha de ingreso

    Parámetros para de sistema para configurar la conexión con la api
        geene_authority_url
        geene_cleint_id
        geene_username
        geene_password
        geene_enpoint
        geene_scope
    """,

    'author': "Interfaces",
    'website': "http://www.interfaces.com.py",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '17.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'contacts', 'account_accountant', 'mantenimiento_registro'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'views/product.xml',
        'views/res_partner.xml',
        'views/aranceles.xml',
        'views/custodia_fisica.xml',
        'views/wizard.xml',
        'data/data.xml',
        'data/cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
