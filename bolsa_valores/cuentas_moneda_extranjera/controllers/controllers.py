# -*- coding: utf-8 -*-
# from odoo import http


# class CuentasMonedaExtranjera(http.Controller):
#     @http.route('/cuentas_moneda_extranjera/cuentas_moneda_extranjera/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/cuentas_moneda_extranjera/cuentas_moneda_extranjera/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('cuentas_moneda_extranjera.listing', {
#             'root': '/cuentas_moneda_extranjera/cuentas_moneda_extranjera',
#             'objects': http.request.env['cuentas_moneda_extranjera.cuentas_moneda_extranjera'].search([]),
#         })

#     @http.route('/cuentas_moneda_extranjera/cuentas_moneda_extranjera/objects/<model("cuentas_moneda_extranjera.cuentas_moneda_extranjera"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('cuentas_moneda_extranjera.object', {
#             'object': obj
#         })
