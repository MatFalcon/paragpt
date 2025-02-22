# -*- coding: utf-8 -*-
# from odoo import http


# class Pbp(http.Controller):
#     @http.route('/pbp/pbp', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/pbp/pbp/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('pbp.listing', {
#             'root': '/pbp/pbp',
#             'objects': http.request.env['pbp.pbp'].search([]),
#         })

#     @http.route('/pbp/pbp/objects/<model("pbp.pbp"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('pbp.object', {
#             'object': obj
#         })
