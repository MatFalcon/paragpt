# -*- coding: utf-8 -*-
# from odoo import http


# class CustodiaFisica(http.Controller):
#     @http.route('/custodia_fisica/custodia_fisica', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/custodia_fisica/custodia_fisica/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('custodia_fisica.listing', {
#             'root': '/custodia_fisica/custodia_fisica',
#             'objects': http.request.env['custodia_fisica.custodia_fisica'].search([]),
#         })

#     @http.route('/custodia_fisica/custodia_fisica/objects/<model("custodia_fisica.custodia_fisica"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('custodia_fisica.object', {
#             'object': obj
#         })
