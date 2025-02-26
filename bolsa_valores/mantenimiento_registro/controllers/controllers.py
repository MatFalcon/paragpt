# -*- coding: utf-8 -*-
# from odoo import http


# class MantenimientoRegistro(http.Controller):
#     @http.route('/mantenimiento_registro/mantenimiento_registro', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mantenimiento_registro/mantenimiento_registro/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mantenimiento_registro.listing', {
#             'root': '/mantenimiento_registro/mantenimiento_registro',
#             'objects': http.request.env['mantenimiento_registro.mantenimiento_registro'].search([]),
#         })

#     @http.route('/mantenimiento_registro/mantenimiento_registro/objects/<model("mantenimiento_registro.mantenimiento_registro"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mantenimiento_registro.object', {
#             'object': obj
#         })
