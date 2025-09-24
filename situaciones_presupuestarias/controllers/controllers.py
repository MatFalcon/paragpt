# -*- coding: utf-8 -*-
# from odoo import http


# class SituacionesPresupuestarias(http.Controller):
#     @http.route('/situaciones_presupuestarias/situaciones_presupuestarias', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/situaciones_presupuestarias/situaciones_presupuestarias/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('situaciones_presupuestarias.listing', {
#             'root': '/situaciones_presupuestarias/situaciones_presupuestarias',
#             'objects': http.request.env['situaciones_presupuestarias.situaciones_presupuestarias'].search([]),
#         })

#     @http.route('/situaciones_presupuestarias/situaciones_presupuestarias/objects/<model("situaciones_presupuestarias.situaciones_presupuestarias"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('situaciones_presupuestarias.object', {
#             'object': obj
#         })
