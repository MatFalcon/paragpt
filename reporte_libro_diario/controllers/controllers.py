# -*- coding: utf-8 -*-
from odoo import http

# class ReporteLibroDiario(http.Controller):
#     @http.route('/reporte_libro_diario/reporte_libro_diario/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/reporte_libro_diario/reporte_libro_diario/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('reporte_libro_diario.listing', {
#             'root': '/reporte_libro_diario/reporte_libro_diario',
#             'objects': http.request.env['reporte_libro_diario.reporte_libro_diario'].search([]),
#         })

#     @http.route('/reporte_libro_diario/reporte_libro_diario/objects/<model("reporte_libro_diario.reporte_libro_diario"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('reporte_libro_diario.object', {
#             'object': obj
#         })