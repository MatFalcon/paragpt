# -*- coding: utf-8 -*-
from odoo import http

# class GrupoAccountPaymentExtra(http.Controller):
#     @http.route('/grupo_account_payment_extra/grupo_account_payment_extra/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/grupo_account_payment_extra/grupo_account_payment_extra/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('grupo_account_payment_extra.listing', {
#             'root': '/grupo_account_payment_extra/grupo_account_payment_extra',
#             'objects': http.request.env['grupo_account_payment_extra.grupo_account_payment_extra'].search([]),
#         })

#     @http.route('/grupo_account_payment_extra/grupo_account_payment_extra/objects/<model("grupo_account_payment_extra.grupo_account_payment_extra"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('grupo_account_payment_extra.object', {
#             'object': obj
#         })