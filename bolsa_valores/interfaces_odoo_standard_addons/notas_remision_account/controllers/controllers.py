# -*- coding: utf-8 -*-
# from odoo import http


# class NotasRemisionAccount(http.Controller):
#     @http.route('/notas_remision_account/notas_remision_account', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/notas_remision_account/notas_remision_account/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('notas_remision_account.listing', {
#             'root': '/notas_remision_account/notas_remision_account',
#             'objects': http.request.env['notas_remision_account.notas_remision_account'].search([]),
#         })

#     @http.route('/notas_remision_account/notas_remision_account/objects/<model("notas_remision_account.notas_remision_account"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('notas_remision_account.object', {
#             'object': obj
#         })
