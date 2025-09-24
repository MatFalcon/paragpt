# -*- coding: utf-8 -*-
# from odoo import http


# class InformeAnalitico(http.Controller):
#     @http.route('/informe_analitico/informe_analitico', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/informe_analitico/informe_analitico/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('informe_analitico.listing', {
#             'root': '/informe_analitico/informe_analitico',
#             'objects': http.request.env['informe_analitico.informe_analitico'].search([]),
#         })

#     @http.route('/informe_analitico/informe_analitico/objects/<model("informe_analitico.informe_analitico"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('informe_analitico.object', {
#             'object': obj
#         })
