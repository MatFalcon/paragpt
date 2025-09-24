# -*- coding: utf-8 -*-
# from odoo import http


# class ActualizacionCliente(http.Controller):
#     @http.route('/actualizacion_cliente/actualizacion_cliente/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/actualizacion_cliente/actualizacion_cliente/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('actualizacion_cliente.listing', {
#             'root': '/actualizacion_cliente/actualizacion_cliente',
#             'objects': http.request.env['actualizacion_cliente.actualizacion_cliente'].search([]),
#         })

#     @http.route('/actualizacion_cliente/actualizacion_cliente/objects/<model("actualizacion_cliente.actualizacion_cliente"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('actualizacion_cliente.object', {
#             'object': obj
#         })
