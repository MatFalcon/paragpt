# -*- coding: utf-8 -*-
from odoo import http

# class AccountCajas(http.Controller):
#     @http.route('/account_cajas/account_cajas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_cajas/account_cajas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_cajas.listing', {
#             'root': '/account_cajas/account_cajas',
#             'objects': http.request.env['account_cajas.account_cajas'].search([]),
#         })

#     @http.route('/account_cajas/account_cajas/objects/<model("account_cajas.account_cajas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_cajas.object', {
#             'object': obj
#         })