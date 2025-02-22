# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaAprobacionCompras(http.Controller):
#     @http.route('/bvpasa_aprobacion_compras/bvpasa_aprobacion_compras', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_aprobacion_compras/bvpasa_aprobacion_compras/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_aprobacion_compras.listing', {
#             'root': '/bvpasa_aprobacion_compras/bvpasa_aprobacion_compras',
#             'objects': http.request.env['bvpasa_aprobacion_compras.bvpasa_aprobacion_compras'].search([]),
#         })

#     @http.route('/bvpasa_aprobacion_compras/bvpasa_aprobacion_compras/objects/<model("bvpasa_aprobacion_compras.bvpasa_aprobacion_compras"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_aprobacion_compras.object', {
#             'object': obj
#         })
