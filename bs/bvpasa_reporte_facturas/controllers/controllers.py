# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaReporteFacturas(http.Controller):
#     @http.route('/bvpasa_reporte_facturas/bvpasa_reporte_facturas', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_reporte_facturas/bvpasa_reporte_facturas/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_reporte_facturas.listing', {
#             'root': '/bvpasa_reporte_facturas/bvpasa_reporte_facturas',
#             'objects': http.request.env['bvpasa_reporte_facturas.bvpasa_reporte_facturas'].search([]),
#         })

#     @http.route('/bvpasa_reporte_facturas/bvpasa_reporte_facturas/objects/<model("bvpasa_reporte_facturas.bvpasa_reporte_facturas"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_reporte_facturas.object', {
#             'object': obj
#         })
