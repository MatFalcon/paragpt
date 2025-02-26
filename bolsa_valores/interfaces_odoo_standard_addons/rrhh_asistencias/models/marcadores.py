from odoo import api, fields, models, exceptions
import datetime, pytz, logging
from odoo.addons.rrhh_asistencias.controllers import controllers as c

_logger = logging.getLogger(__name__)


class Marcadores(models.Model):
    _name = 'rrhh_asistencias.marcadores'

    name = fields.Char('Nombre del marcador', required=True)
    company_id = fields.Many2one('res.company', string='Compañía')
    codigo_interno = fields.Char('Código interno')
    ip_address = fields.Char('Dirección IP', required=True)
    port = fields.Integer('Puerto', default=4370, required=True)
    usuario = fields.Char('Usuario')
    device_password = fields.Integer('Password')
    active = fields.Boolean(string='Active', default=True)

    def test_connection(self):
        # rrhh_asistencias/models/marcadores.py
        with c.ConnectToDevice(self.ip_address, self.port, self.device_password) as conn:
            if conn:
                # return {
                #     "type": "ir.actions.act_window",
                #     "res_model": "devices",
                #     "views": [[False, "form"]],
                #     "res_id": self.id,
                #     "target": "main",
                #     "context": {'show_message1': True},
                # }
                print('Reloj conectado')

    def get_attendances(self):
        # rrhh_asistencias/models/marcadores.py
        ids_unicos = self.env['rrhh_asistencias.marcaciones'].search([('id_unico_marcacion', '!=', False)]).mapped(
            'id_unico_marcacion')
        for this in self:
            with c.ConnectToDevice(this.ip_address, this.port, this.device_password) as conn:
                if conn:
                    _logger.info('Obteniendo las marcaciones del reloj ' + this.name)
                    attendances = conn.get_attendance()
                    _logger.info('Marcaciones obtenidas del reloj ' + this.name)
                    for attendance in attendances:
                        fecha_hora_real = pytz.timezone('America/Asuncion').localize(attendance.timestamp)
                        fecha_hora_utc = fecha_hora_real.astimezone(pytz.timezone('UTC'))

                        id_unico = attendance.user_id + str(attendance.timestamp)
                        if id_unico not in ids_unicos:
                            _logger.info('Procesando marcación ' + id_unico)
                            self.env['rrhh_asistencias.marcaciones'].create({
                                'id_unico_marcacion': id_unico,
                                'id_marcacion': attendance.user_id,
                                'id_marcador': this.id,
                                'raw_fecha_hora': datetime.datetime.strftime(fecha_hora_utc, '%Y-%m-%d %H:%M:%S'),
                            })
                            self._cr.commit()
                            ids_unicos.append(id_unico)
                    # conn.clear_attendance()

    # def button_obtener_marcaciones(self):
    #     zk = zklib.ZKLib(self.ip_address, int(self.port))
    #     ret = zk.connect()
    #     if ret == True:
    #         zk.disableDevice()
    #         attendance = zk.getAttendance()
    #         for i in attendance:
    #             fecha_hora = i[2]
    #             hora = fecha_hora.hour + fecha_hora.minute / 60
    #             marcacion = {
    #                 'id_marcador': self.id,
    #                 'id_marcacion': i[0],
    #                 'raw_fecha_hora': fecha_hora,
    #                 'fecha': datetime.strftime(fecha_hora, '%Y-%m-%d'),
    #                 'hora': hora
    #             }
    #             if str(fecha_hora) > "2019-10-21 07:16:17":
    #                 self.env['interfaces_payroll.marcaciones'].create(marcacion)
    #         zk.clearAttendance()
    #         zk.enableDevice()
    #         zk.disconnect()
    #

    def obtener_marcaciones_cron(self):
        # rrhh_asistencias/models/marcadores.py
        marcadores = self.env['rrhh_asistencias.marcadores'].search([('active', '=', True)])
        for i in marcadores:
            i.get_attendances()
        return
