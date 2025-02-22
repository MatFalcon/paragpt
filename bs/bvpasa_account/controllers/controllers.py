# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaAccount(http.Controller):
#     @http.route('/bvpasa_account/bvpasa_account', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_account/bvpasa_account/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_account.listing', {
#             'root': '/bvpasa_account/bvpasa_account',
#             'objects': http.request.env['bvpasa_account.bvpasa_account'].search([]),
#         })

#     @http.route('/bvpasa_account/bvpasa_account/objects/<model("bvpasa_account.bvpasa_account"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_account.object', {
#             'object': obj
#         })
