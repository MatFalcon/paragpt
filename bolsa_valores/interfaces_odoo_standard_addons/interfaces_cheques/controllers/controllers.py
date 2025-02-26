# -*- coding: utf-8 -*-
# from odoo import http


# class InterfacesCheques(http.Controller):
#     @http.route('/interfaces_cheques/interfaces_cheques/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/interfaces_cheques/interfaces_cheques/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('interfaces_cheques.listing', {
#             'root': '/interfaces_cheques/interfaces_cheques',
#             'objects': http.request.env['interfaces_cheques.interfaces_cheques'].search([]),
#         })

#     @http.route('/interfaces_cheques/interfaces_cheques/objects/<model("interfaces_cheques.interfaces_cheques"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('interfaces_cheques.object', {
#             'object': obj
#         })
