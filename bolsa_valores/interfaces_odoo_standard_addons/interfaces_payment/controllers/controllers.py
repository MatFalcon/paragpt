# -*- coding: utf-8 -*-
# from odoo import http


# class InterfacesPayment(http.Controller):
#     @http.route('/interfaces_payment/interfaces_payment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/interfaces_payment/interfaces_payment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('interfaces_payment.listing', {
#             'root': '/interfaces_payment/interfaces_payment',
#             'objects': http.request.env['interfaces_payment.interfaces_payment'].search([]),
#         })

#     @http.route('/interfaces_payment/interfaces_payment/objects/<model("interfaces_payment.interfaces_payment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('interfaces_payment.object', {
#             'object': obj
#         })
