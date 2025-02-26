# -*- coding: utf-8 -*-
# from odoo import http


# class L10nPyReports(http.Controller):
#     @http.route('/l10n_py_reports/l10n_py_reports', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/l10n_py_reports/l10n_py_reports/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('l10n_py_reports.listing', {
#             'root': '/l10n_py_reports/l10n_py_reports',
#             'objects': http.request.env['l10n_py_reports.l10n_py_reports'].search([]),
#         })

#     @http.route('/l10n_py_reports/l10n_py_reports/objects/<model("l10n_py_reports.l10n_py_reports"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('l10n_py_reports.object', {
#             'object': obj
#         })
