from odoo import http
import os


class Res90(http.Controller):
    @http.route('/res90/download_file/', auth='public')
    def index(self, **kw):
        if kw.get('file'):
            filepath = os.path.join('/tmp/' + kw.get('file'))
            r = http.send_file(filepath, kw.get('file') + '.txt', as_attachment=True, filename=kw.get('filename'))

            return r

#     @http.route('/resolucion_90/resolucion_90/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('resolucion_90.listing', {
#             'root': '/resolucion_90/resolucion_90',
#             'objects': http.request.env['resolucion_90.resolucion_90'].search([]),
#         })

#     @http.route('/resolucion_90/resolucion_90/objects/<model("resolucion_90.resolucion_90"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('resolucion_90.object', {
#             'object': obj
#         })
