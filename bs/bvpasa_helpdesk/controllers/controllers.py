# -*- coding: utf-8 -*-
# from odoo import http


# class BvpasaHelpdesk(http.Controller):
#     @http.route('/bvpasa_helpdesk/bvpasa_helpdesk', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bvpasa_helpdesk/bvpasa_helpdesk/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bvpasa_helpdesk.listing', {
#             'root': '/bvpasa_helpdesk/bvpasa_helpdesk',
#             'objects': http.request.env['bvpasa_helpdesk.bvpasa_helpdesk'].search([]),
#         })

#     @http.route('/bvpasa_helpdesk/bvpasa_helpdesk/objects/<model("bvpasa_helpdesk.bvpasa_helpdesk"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bvpasa_helpdesk.object', {
#             'object': obj
#         })
