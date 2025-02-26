# -*- coding: utf-8 -*-
# from odoo import http


# class DerivacionTickets(http.Controller):
#     @http.route('/derivacion_tickets/derivacion_tickets/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/derivacion_tickets/derivacion_tickets/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('derivacion_tickets.listing', {
#             'root': '/derivacion_tickets/derivacion_tickets',
#             'objects': http.request.env['derivacion_tickets.derivacion_tickets'].search([]),
#         })

#     @http.route('/derivacion_tickets/derivacion_tickets/objects/<model("derivacion_tickets.derivacion_tickets"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('derivacion_tickets.object', {
#             'object': obj
#         })
