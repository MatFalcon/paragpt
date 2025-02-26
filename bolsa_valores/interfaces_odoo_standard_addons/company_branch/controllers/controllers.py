# -*- coding: utf-8 -*-
# from odoo import http


# class CompanyBranch(http.Controller):
#     @http.route('/company_branch/company_branch', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/company_branch/company_branch/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('company_branch.listing', {
#             'root': '/company_branch/company_branch',
#             'objects': http.request.env['company_branch.company_branch'].search([]),
#         })

#     @http.route('/company_branch/company_branch/objects/<model("company_branch.company_branch"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('company_branch.object', {
#             'object': obj
#         })
