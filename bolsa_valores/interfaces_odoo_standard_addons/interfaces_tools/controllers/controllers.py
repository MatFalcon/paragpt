# -*- coding: utf-8 -*-
# from odoo import http


# class InterfacesTools(http.Controller):
#     @http.route('/interfaces_tools/interfaces_tools', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/interfaces_tools/interfaces_tools/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('interfaces_tools.listing', {
#             'root': '/interfaces_tools/interfaces_tools',
#             'objects': http.request.env['interfaces_tools.interfaces_tools'].search([]),
#         })

#     @http.route('/interfaces_tools/interfaces_tools/objects/<model("interfaces_tools.interfaces_tools"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('interfaces_tools.object', {
#             'object': obj
#         })
