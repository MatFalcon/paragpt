# -*- coding: utf-8 -*-
{
    "name": "Readonly User", 
    'category': 'Extra Tools',
    "summary": "For Dynamic Readonly View For Users",
    "description": """This module enables the feature to readonly features user wise
    
    Read only user
    read only
    limited user
    restrict create
    restrict edit
    restrict delete
    restrict duplicate
    restrict record
    readonly

    """,
    'version': '15.0',
    'author': "Crest Infosys",
    'license': 'OPL-1',
    'depends': ['web', 'base'],
    'data': [
        'security/readonly_user_security.xml',
        'views/res_user_view.xml',
    ],
    # 'images': ['static/description/main_screenshot.png'],
    'price': 7.0,
    'currency': 'EUR',
    'installable': True,
    'application': True,
    'auto_install': False
}