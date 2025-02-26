# -*- coding: utf-8 -*-
# from odoo import http


# class NotasRemision(http.Controller):
#     @http.route('/notas_remision/notas_remision/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/notas_remision/notas_remision/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('notas_remision.listing', {
#             'root': '/notas_remision/notas_remision',
#             'objects': http.request.env['notas_remision.notas_remision'].search([]),
#         })

#     @http.route('/notas_remision/notas_remision/objects/<model("notas_remision.notas_remision"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('notas_remision.object', {
#             'object': obj
#         })
