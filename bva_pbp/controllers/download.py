from odoo import http
from odoo.http import request
import base64

class ReporteDevengamientoController(http.Controller):

    @http.route('/download/reporte_devengamiento/<int:record_id>', type='http', auth='user')
    def download_reporte_devengamiento(self, record_id, **kwargs):
        # Buscar el registro de cartera de inversión
        record = request.env['pbp.cartera_inversion'].sudo().browse(record_id)
        if not record or not record.reporte_excel:
            return request.not_found()

        # Decodificar el archivo de base64
        file_content = base64.b64decode(record.reporte_excel)
        filename = record.reporte_nombre or 'Reporte_Devengamiento.xlsx'

        # Retornar el archivo como respuesta HTTP para descarga
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]
        )


class ReporteVencimientosController(http.Controller):

    @http.route('/download/reporte_vencimientos/<int:record_id>', type='http', auth='user')
    def download_reporte_devengamiento(self, record_id, **kwargs):
        # Buscar el registro de cartera de inversión
        record = request.env['pbp.wizard.vencimientos.report'].sudo().browse(record_id)
        if not record or not record.reporte_excel:
            return request.not_found()

        # Decodificar el archivo de base64
        file_content = base64.b64decode(record.reporte_excel)
        filename = 'Reporte_Devengamiento.xlsx'

        # Retornar el archivo como respuesta HTTP para descarga
        return request.make_response(
            file_content,
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', f'attachment; filename="{filename}"')
            ]
        )
