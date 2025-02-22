# -*- coding: utf-8 -*-
# from odoo import http


# class IntegracionApiContinental(http.Controller):
#     @http.route('/integracion_api_continental/integracion_api_continental', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/integracion_api_continental/integracion_api_continental/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('integracion_api_continental.listing', {
#             'root': '/integracion_api_continental/integracion_api_continental',
#             'objects': http.request.env['integracion_api_continental.integracion_api_continental'].search([]),
#         })

#     @http.route('/integracion_api_continental/integracion_api_continental/objects/<model("integracion_api_continental.integracion_api_continental"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('integracion_api_continental.object', {
#             'object': obj
#         })
