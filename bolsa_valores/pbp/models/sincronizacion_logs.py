import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class SincronizacionLogs(models.Model):
    _name = 'pbp.sincronizacion_logs'
    _description = 'Se guardan los registros de cada sincronización realizada'

    name = fields.Char(string="Nombre")
    tipo_sincronizacion = fields.Char(string='Tipo Sincronizacion')
    error_msg = fields.Char(string='Mensaje de error')
    fecha_sincronizacion = fields.Date(string='Fecha de Sincronizacion')
    cant_registros_obtenidos = fields.Integer(string='Cant. de registros obtenidos')
    sincronizacion_correcta = fields.Boolean(string='Sincronización correcta', default=True)
    registros_fallidos = fields.Integer(string="Registros fallidos", default=0, compute="compute_registros_fallidos")

    detalle_ids = fields.One2many('pbp.sincronizacion_detalle_logs', 'sincronizacion', string='Detalles de Errores')

    def compute_registros_fallidos(self):
        for i in self:
            if i.detalle_ids:
                i.registros_fallidos = len(i.detalle_ids)
            else:
                i.registros_fallidos = 0


class SincronizacionDetalleLogs(models.Model):
    _name = 'pbp.sincronizacion_detalle_logs'
    _description = 'Se guardan los detalles de cada sincronización realizada'

    sincronizacion = fields.Many2one('pbp.sincronizacion_logs', string='Sincronización')
    registro = fields.Char(string='Registro')
    error_msg = fields.Char(string='Mensaje de error')