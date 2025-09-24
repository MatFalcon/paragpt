# -*- coding: utf-8 -*-
# from odoo import http


# class VencimientoContrato(http.Controller):
#     @http.route('/vencimiento_contrato/vencimiento_contrato/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/vencimiento_contrato/vencimiento_contrato/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('vencimiento_contrato.listing', {
#             'root': '/vencimiento_contrato/vencimiento_contrato',
#             'objects': http.request.env['vencimiento_contrato.vencimiento_contrato'].search([]),
#         })

#     @http.route('/vencimiento_contrato/vencimiento_contrato/objects/<model("vencimiento_contrato.vencimiento_contrato"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('vencimiento_contrato.object', {
#             'object': obj
#         })
