# -*- coding: utf-8 -*-
# from odoo import http


# class ConciliacionAutomatica(http.Controller):
#     @http.route('/conciliacion_automatica/conciliacion_automatica', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/conciliacion_automatica/conciliacion_automatica/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('conciliacion_automatica.listing', {
#             'root': '/conciliacion_automatica/conciliacion_automatica',
#             'objects': http.request.env['conciliacion_automatica.conciliacion_automatica'].search([]),
#         })

#     @http.route('/conciliacion_automatica/conciliacion_automatica/objects/<model("conciliacion_automatica.conciliacion_automatica"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('conciliacion_automatica.object', {
#             'object': obj
#         })
