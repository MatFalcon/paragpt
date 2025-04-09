# © 2016 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Pagos contados en facturas",
    "version": "17.0.1.4.0",
    "category": "Accounting",
    "website": "www.sati.com.py",
    "author": "SATI",
    "license": "AGPL-3",
    "application": False,
    'installable': True,
    "depends": [
        "account",
    ],
    "data": [
        'security/security.xml',
        'views/account_move_line_view.xml',
    ],
}
