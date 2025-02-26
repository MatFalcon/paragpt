# -*- coding: utf-8 -*-
# from odoo import http


# class CysaProduct(http.Controller):
#     @http.route('/cysa_product/cysa_product/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cysa_product/cysa_product/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cysa_product.listing', {
#             'root': '/cysa_product/cysa_product',
#             'objects': http.request.env['cysa_product.cysa_product'].search([]),
#         })

#     @http.route('/cysa_product/cysa_product/objects/<model("cysa_product.cysa_product"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cysa_product.object', {
#             'object': obj
#         })
