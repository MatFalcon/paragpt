# -*- coding: utf-8 -*-
from odoo import http
import hashlib

class FacturaAutoimpresor(http.Controller):
    @http.route('/invoice_check', auth='public', website=True)
    def index(self,invoice_id,token):
        if token==self.genera_token(str(invoice_id)):
            invoice=http.request.env['account.move'].sudo().search([('id','=',int(invoice_id))])
            return http.request.render('factura_autoimpresor.online_invoice',{'invoice':invoice})
        else:
            return http.request.render('factura_autoimpresor.token_invalido')

    def genera_token(self,id_factura):
        palabra=id_factura+"amakakeruriunohirameki"
        return hashlib.sha256(bytes(palabra,'utf-8')).hexdigest()

#     @http.route('/factura_autoimpresor/factura_autoimpresor/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('factura_autoimpresor.listing', {
#             'root': '/factura_autoimpresor/factura_autoimpresor',
#             'objects': http.request.env['factura_autoimpresor.factura_autoimpresor'].search([]),
#         })

#     @http.route('/factura_autoimpresor/factura_autoimpresor/objects/<model("factura_autoimpresor.factura_autoimpresor"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('factura_autoimpresor.object', {
#             'object': obj
#         })
