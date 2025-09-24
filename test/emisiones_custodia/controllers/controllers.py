# -*- coding: utf-8 -*-
# from odoo import http


# class EmisionesCustodia(http.Controller):
#     @http.route('/emisiones_custodia/emisiones_custodia', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/emisiones_custodia/emisiones_custodia/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('emisiones_custodia.listing', {
#             'root': '/emisiones_custodia/emisiones_custodia',
#             'objects': http.request.env['emisiones_custodia.emisiones_custodia'].search([]),
#         })

#     @http.route('/emisiones_custodia/emisiones_custodia/objects/<model("emisiones_custodia.emisiones_custodia"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('emisiones_custodia.object', {
#             'object': obj
#         })
