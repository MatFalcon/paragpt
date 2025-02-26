# -*- coding: utf-8 -*-
# from odoo import http


# class L10nPy(http.Controller):
#     @http.route('/l10n_py/l10n_py', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_py/l10n_py/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_py.listing', {
#             'root': '/l10n_py/l10n_py',
#             'objects': http.request.env['l10n_py.l10n_py'].search([]),
#         })

#     @http.route('/l10n_py/l10n_py/objects/<model("l10n_py.l10n_py"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_py.object', {
#             'object': obj
#         })
