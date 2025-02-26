# -*- coding: utf-8 -*-
from odoo import http

# class InterfacesTimbrado(http.Controller):
#     @http.route('/interfaces_timbrado/interfaces_timbrado/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/interfaces_timbrado/interfaces_timbrado/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('interfaces_timbrado.listing', {
#             'root': '/interfaces_timbrado/interfaces_timbrado',
#             'objects': http.request.env['interfaces_timbrado.interfaces_timbrado'].search([]),
#         })

#     @http.route('/interfaces_timbrado/interfaces_timbrado/objects/<model("interfaces_timbrado.interfaces_timbrado"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('interfaces_timbrado.object', {
#             'object': obj
#         })