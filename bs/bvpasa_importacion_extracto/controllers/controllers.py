# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaImportacionExtracto(http.Controller):
#     @http.route('/bvpasa_importacion_extracto/bvpasa_importacion_extracto', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_importacion_extracto/bvpasa_importacion_extracto/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_importacion_extracto.listing', {
#             'root': '/bvpasa_importacion_extracto/bvpasa_importacion_extracto',
#             'objects': http.request.env['bvpasa_importacion_extracto.bvpasa_importacion_extracto'].search([]),
#         })

#     @http.route('/bvpasa_importacion_extracto/bvpasa_importacion_extracto/objects/<model("bvpasa_importacion_extracto.bvpasa_importacion_extracto"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_importacion_extracto.object', {
#             'object': obj
#         })
