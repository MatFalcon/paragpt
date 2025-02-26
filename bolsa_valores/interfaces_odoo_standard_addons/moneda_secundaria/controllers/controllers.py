# -*- coding: utf-8 -*-
# from odoo import http


# class TipoCambioCalculado(http.Controller):
#     @http.route('/tipo_cambio_calculado/tipo_cambio_calculado', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tipo_cambio_calculado/tipo_cambio_calculado/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tipo_cambio_calculado.listing', {
#             'root': '/tipo_cambio_calculado/tipo_cambio_calculado',
#             'objects': http.request.env['tipo_cambio_calculado.tipo_cambio_calculado'].search([]),
#         })

#     @http.route('/tipo_cambio_calculado/tipo_cambio_calculado/objects/<model("tipo_cambio_calculado.tipo_cambio_calculado"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tipo_cambio_calculado.object', {
#             'object': obj
#         })
