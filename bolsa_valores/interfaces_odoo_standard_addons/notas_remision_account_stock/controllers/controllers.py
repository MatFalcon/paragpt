# -*- coding: utf-8 -*-
# from odoo import http


# class NotasRemisionAccountStock(http.Controller):
#     @http.route('/notas_remision_account_stock/notas_remision_account_stock', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/notas_remision_account_stock/notas_remision_account_stock/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('notas_remision_account_stock.listing', {
#             'root': '/notas_remision_account_stock/notas_remision_account_stock',
#             'objects': http.request.env['notas_remision_account_stock.notas_remision_account_stock'].search([]),
#         })

#     @http.route('/notas_remision_account_stock/notas_remision_account_stock/objects/<model("notas_remision_account_stock.notas_remision_account_stock"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('notas_remision_account_stock.object', {
#             'object': obj
#         })
