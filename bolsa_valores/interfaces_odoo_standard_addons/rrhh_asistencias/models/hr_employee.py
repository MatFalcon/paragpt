from odoo import fields, api, models, exceptions, _
import pytz


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    id_marcacion = fields.Integer(string="ID de marcación")
    no_attendance_is_absence = fields.Boolean(string='Falta de marcación es ausencia', default=True,
                                              help='Cuando se procesa una nómina, si no se encuentra una asistencia para una fecha determinada se considera como una ausencia')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def _attendance_action_change(self):
        # rrhh_asistencias/models/hr_employee.py
        self.ensure_one()
        action_date = fields.Datetime.now()
        fecha, hora = self.env['rrhh_asistencias.marcaciones'].process_date(raw_fecha_hora=action_date)
        attendance = self.env['rrhh_asistencias.marcaciones'].create_attendance(
            employee_id=self,
            fecha=fecha,
            hora=hora
        )
        return attendance

    def _compute_hours_today(self):
        # rrhh_asistencias/models/hr_employee.py
        now = fields.Datetime.now()
        fecha, hora = self.env['rrhh_asistencias.marcaciones'].process_date(raw_fecha_hora=now)
        for employee in self:
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('date', '=', fecha),
                '|',
                ('salida_marcada', '=', False),
                ('salida_marcada', '=', 0),
            ])
            worked_hours = 0
            for attendance in attendances:
                worked_hours = +hora - attendance.entrada_marcada
            employee.hours_today = worked_hours

    def _compute_attendance_state(self):
        # rrhh_asistencias/models/hr_employee.py
        now = fields.Datetime.now()
        fecha, hora = self.env['rrhh_asistencias.marcaciones'].process_date(raw_fecha_hora=now)
        for employee in self:
            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('date', '=', fecha),
                '|',
                ('salida_marcada', '=', False),
                ('salida_marcada', '=', 0),
            ])
            employee.attendance_state = 'checked_in' if attendances else 'checked_out'
