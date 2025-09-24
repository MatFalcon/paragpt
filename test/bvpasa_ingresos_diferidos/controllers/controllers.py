# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaIngresosDiferidos(http.Controller):
#     @http.route('/bvpasa_ingresos_diferidos/bvpasa_ingresos_diferidos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_ingresos_diferidos/bvpasa_ingresos_diferidos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_ingresos_diferidos.listing', {
#             'root': '/bvpasa_ingresos_diferidos/bvpasa_ingresos_diferidos',
#             'objects': http.request.env['bvpasa_ingresos_diferidos.bvpasa_ingresos_diferidos'].search([]),
#         })

#     @http.route('/bvpasa_ingresos_diferidos/bvpasa_ingresos_diferidos/objects/<model("bvpasa_ingresos_diferidos.bvpasa_ingresos_diferidos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_ingresos_diferidos.object', {
#             'object': obj
#         })
