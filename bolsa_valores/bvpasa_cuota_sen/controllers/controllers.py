# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaCuotaSen(http.Controller):
#     @http.route('/bvpasa_cuota_sen/bvpasa_cuota_sen', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_cuota_sen/bvpasa_cuota_sen/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_cuota_sen.listing', {
#             'root': '/bvpasa_cuota_sen/bvpasa_cuota_sen',
#             'objects': http.request.env['bvpasa_cuota_sen.bvpasa_cuota_sen'].search([]),
#         })

#     @http.route('/bvpasa_cuota_sen/bvpasa_cuota_sen/objects/<model("bvpasa_cuota_sen.bvpasa_cuota_sen"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_cuota_sen.object', {
#             'object': obj
#         })
