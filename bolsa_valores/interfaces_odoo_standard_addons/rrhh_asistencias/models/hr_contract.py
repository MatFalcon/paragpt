from odoo import fields, api, models, exceptions


class HrContract(models.Model):
    _inherit = 'hr.contract'

    def get_resource_calendar_id_fecha(self, date):
        # rrhh_asistencias/models/hr_contract.py
        domain = [
            ('date_from', '<=', date),
            ('date_to', '>=', date),
        ]
        hr_attendance_calendar_id = self.env['hr.attendance.calendar'].sudo().search(domain + [
            ('applied_on', '=', 'employee'),
            ('contract_id', '=', self.id),
        ], limit=1)
        if not hr_attendance_calendar_id:
            hr_attendance_calendar_id = self.env['hr.attendance.calendar'].sudo().search(domain + [
                ('applied_on', '=', 'department'),
                ('department_id', '=', self.department_id.id),
            ], limit=1)

        if hr_attendance_calendar_id:
            resource_calendar_id = hr_attendance_calendar_id.resource_calendar_id
        else:
            resource_calendar_id = self.resource_calendar_id
        return resource_calendar_id

    def get_entrada_planeada(self, date, day_period=False):
        # rrhh_asistencias/models/hr_contract.py
        resource_calendar_id = self.get_resource_calendar_id_fecha(date)
        lineas_entrada_planeada = resource_calendar_id.attendance_ids.filtered(
            lambda linea:
            int(linea.dayofweek) == date.weekday()
        )
        if day_period and 'morning' in lineas_entrada_planeada.mapped('day_period'):
            lineas_entrada_planeada = lineas_entrada_planeada.filtered(lambda linea: linea.day_period == day_period)
        return min(lineas_entrada_planeada.mapped('hour_from')) if lineas_entrada_planeada else False

    def get_salida_planeada(self, date, day_period=False):
        # rrhh_asistencias/models/hr_contract.py
        resource_calendar_id = self.get_resource_calendar_id_fecha(date)
        lineas_salida_planeada = resource_calendar_id.attendance_ids.filtered(
            lambda linea:
            int(linea.dayofweek) == date.weekday()
        )
        if day_period and 'morning' in lineas_salida_planeada.mapped('day_period'):
            lineas_salida_planeada = lineas_salida_planeada.filtered(lambda linea: linea.day_period == day_period)
        return max(lineas_salida_planeada.mapped('hour_to')) if lineas_salida_planeada else False

    def get_turno_planeado(self, date, day_period=False):
        # rrhh_asistencias/models/hr_contract.py
        resource_calendar_id = self.get_resource_calendar_id_fecha(date)
        lineas_salida_planeada = resource_calendar_id.attendance_ids.filtered(
            lambda linea:
            int(linea.dayofweek) == date.weekday()
        )
        if day_period and 'morning' in lineas_salida_planeada.mapped('day_period'):
            lineas_salida_planeada = lineas_salida_planeada.filtered(lambda linea: linea.day_period == day_period)
        return max(lineas_salida_planeada.mapped('day_period')) if lineas_salida_planeada else False

    @api.constrains('employee_id', 'state', 'kanban_state', 'date_start', 'date_end')
    def _check_current_contract(self):
        # rrhh_asistencias/models/hr_contract.py
        return
