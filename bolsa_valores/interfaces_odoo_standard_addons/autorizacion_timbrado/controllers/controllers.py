# -*- coding: utf-8 -*-
# from odoo import http


# class AutorizacionTimbrado(http.Controller):
#     @http.route('/autorizacion_timbrado/autorizacion_timbrado/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/autorizacion_timbrado/autorizacion_timbrado/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('autorizacion_timbrado.listing', {
#             'root': '/autorizacion_timbrado/autorizacion_timbrado',
#             'objects': http.request.env['autorizacion_timbrado.autorizacion_timbrado'].search([]),
#         })

#     @http.route('/autorizacion_timbrado/autorizacion_timbrado/objects/<model("autorizacion_timbrado.autorizacion_timbrado"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('autorizacion_timbrado.object', {
#             'object': obj
#         })
