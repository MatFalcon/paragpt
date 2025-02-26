# -*- coding: utf-8 -*-
# from odoo import http


# class CuotasProyectos(http.Controller):
#     @http.route('/cuotas_proyectos/cuotas_proyectos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cuotas_proyectos/cuotas_proyectos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('cuotas_proyectos.listing', {
#             'root': '/cuotas_proyectos/cuotas_proyectos',
#             'objects': http.request.env['cuotas_proyectos.cuotas_proyectos'].search([]),
#         })

#     @http.route('/cuotas_proyectos/cuotas_proyectos/objects/<model("cuotas_proyectos.cuotas_proyectos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cuotas_proyectos.object', {
#             'object': obj
#         })
