# -*- coding: utf-8 -*-
# from odoo import http


# class ProveedoresTimbrado(http.Controller):
#     @http.route('/proveedores_timbrado/proveedores_timbrado/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/proveedores_timbrado/proveedores_timbrado/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('proveedores_timbrado.listing', {
#             'root': '/proveedores_timbrado/proveedores_timbrado',
#             'objects': http.request.env['proveedores_timbrado.proveedores_timbrado'].search([]),
#         })

#     @http.route('/proveedores_timbrado/proveedores_timbrado/objects/<model("proveedores_timbrado.proveedores_timbrado"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('proveedores_timbrado.object', {
#             'object': obj
#         })
