# -*- coding: utf-8 -*-
# from odoo import http


# class InterfacesPurchase(http.Controller):
#     @http.route('/interfaces_purchase/interfaces_purchase', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/interfaces_purchase/interfaces_purchase/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('interfaces_purchase.listing', {
#             'root': '/interfaces_purchase/interfaces_purchase',
#             'objects': http.request.env['interfaces_purchase.interfaces_purchase'].search([]),
#         })

#     @http.route('/interfaces_purchase/interfaces_purchase/objects/<model("interfaces_purchase.interfaces_purchase"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('interfaces_purchase.object', {
#             'object': obj
#         })
