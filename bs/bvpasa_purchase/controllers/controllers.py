# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaPresupuestos(http.Controller):
#     @http.route('/bvpasa_presupuestos/bvpasa_presupuestos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_presupuestos/bvpasa_presupuestos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_presupuestos.listing', {
#             'root': '/bvpasa_presupuestos/bvpasa_presupuestos',
#             'objects': http.request.env['bvpasa_presupuestos.bvpasa_presupuestos'].search([]),
#         })

#     @http.route('/bvpasa_presupuestos/bvpasa_presupuestos/objects/<model("bvpasa_presupuestos.bvpasa_presupuestos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_presupuestos.object', {
#             'object': obj
#         })
