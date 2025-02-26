# -*- coding: utf-8 -*-
# from odoo import http


# class CuotasAlumnos(http.Controller):
#     @http.route('/cuotas/cuotas/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cuotas/cuotas/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cuotas.listing', {
#             'root': '/cuotas/cuotas',
#             'objects': http.request.env['cuotas.cuotas'].search([]),
#         })

#     @http.route('/cuotas/cuotas/objects/<model("cuotas.cuotas"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cuotas.object', {
#             'object': obj
#         })
