# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaIntegracionBancard(http.Controller):
#     @http.route('/bvpasa_integracion_bancard/bvpasa_integracion_bancard', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_integracion_bancard/bvpasa_integracion_bancard/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_integracion_bancard.listing', {
#             'root': '/bvpasa_integracion_bancard/bvpasa_integracion_bancard',
#             'objects': http.request.env['bvpasa_integracion_bancard.bvpasa_integracion_bancard'].search([]),
#         })

#     @http.route('/bvpasa_integracion_bancard/bvpasa_integracion_bancard/objects/<model("bvpasa_integracion_bancard.bvpasa_integracion_bancard"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_integracion_bancard.object', {
#             'object': obj
#         })
