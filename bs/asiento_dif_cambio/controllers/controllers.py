# -*- coding: utf-8 -*-
# from odoo import http


# class AsientoDifCambio(http.Controller):
#     @http.route('/asiento_dif_cambio/asiento_dif_cambio', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/asiento_dif_cambio/asiento_dif_cambio/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('asiento_dif_cambio.listing', {
#             'root': '/asiento_dif_cambio/asiento_dif_cambio',
#             'objects': http.request.env['asiento_dif_cambio.asiento_dif_cambio'].search([]),
#         })

#     @http.route('/asiento_dif_cambio/asiento_dif_cambio/objects/<model("asiento_dif_cambio.asiento_dif_cambio"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('asiento_dif_cambio.object', {
#             'object': obj
#         })
