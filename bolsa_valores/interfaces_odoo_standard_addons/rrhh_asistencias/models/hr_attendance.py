from odoo import fields, api, models, exceptions, _
from odoo.tools import format_datetime
import pytz, datetime


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    _order = 'date desc, entrada_marcada desc'

    contract_id = fields.Many2one('hr.contract', string='Contrato', required=True)
    id_marcador = fields.Many2one('rrhh_asistencias.marcadores')
    active = fields.Boolean(default=True)
    date = fields.Date(string='Fecha')
    entrada_marcada = fields.Float(string='Marcación Entrada')
    salida_marcada = fields.Float(string='Marcación Salida')
    full_check_in = fields.Datetime(string='Marcación entrada con fecha', compute='get_full_check_in_out')
    full_check_out = fields.Datetime(string='Marcación Salida con fecha', compute='get_full_check_in_out')
    resource_calendar_id = fields.Many2one('resource.calendar', string='Planeamiento de Asistencias', compute='get_entrada_salida_planeada')
    entrada_planeada = fields.Float(string='Entrada Planeada', compute='get_entrada_salida_planeada')
    salida_planeada = fields.Float(string='Salida Planeada', compute='get_entrada_salida_planeada')
    day_period = fields.Selection(string='Periodo del día', selection=[('morning', 'Mañana'), ('afternoon', 'Tarde'), ], compute='get_entrada_salida_planeada')
    asistencia_fuera_de_planeado = fields.Boolean(string='Fuera de Planeado', compute='get_asistencia_fuera_de_planeado_feriado')
    asistencia_feriado = fields.Boolean(string='Asistencia en Feriado', compute='get_asistencia_fuera_de_planeado_feriado')

    horas_extra_50 = fields.Float(string='Horas extra 50%', compute='_get_llegada_anticipada_tardia_extra')
    horas_extra_100 = fields.Float(string='Horas extra 100%', compute='_get_llegada_anticipada_tardia_extra')
    horas_extra_nocturnas = fields.Float(string='Horas extra Nocturnas', compute='_get_llegada_anticipada_tardia_extra')
    horas_nocturnas = fields.Float(string='Horas Nocturnas', compute='_get_llegada_anticipada_tardia_extra')
    se_procesa_horas_extra_50 = fields.Boolean(string='Se procesa horas extra 50%', default=False)
    se_procesa_horas_extra_100 = fields.Boolean(string='Se procesa horas extra 100%', default=False)
    se_procesa_horas_extra_nocturnas = fields.Boolean(string='Se procesa horas nocturnas', default=False)
    se_procesa_horas_nocturnas = fields.Boolean(string='Se procesa horas nocturnas', default=False)

    llegada_anticipada = fields.Float(string='Llegada anticipada', compute='_get_llegada_anticipada_tardia_extra')
    llegada_tardia = fields.Float(string='Llegada tardía', compute='_get_llegada_anticipada_tardia_extra')
    salida_anticipada = fields.Float(string='Salida anticipada', compute='_get_llegada_anticipada_tardia_extra')
    total_plus_horario = fields.Float(string='Horas plus', compute='_get_llegada_anticipada_tardia_extra')
    total_mix_horario = fields.Float(string='Horas mixtas', compute='_get_llegada_anticipada_tardia_extra')
    es_plus_horario = fields.Boolean(string='Esta en horario plus', default=False)
    es_mix_horario = fields.Boolean(string='Esta en horario mixto', default=False)
    se_procesa_llegada_anticipada = fields.Boolean(string='Se procesa llegada anticipada', default=False)
    se_procesa_llegada_tardia = fields.Boolean(string='Se procesa llegada tardia', default=False)
    se_procesa_salida_anticipada = fields.Boolean(string='Se procesa salida anticipada', default=False)
    se_procesa_plus_hora = fields.Boolean(string='Se procesa plus de horas', default=False)
    se_procesa_mix_hora = fields.Boolean(string='Se procesa horario mixto', default=False)

    def get_auto_checks(self):
        if self.resource_calendar_id and not self.resource_calendar_id.allow_auto_checks:
            return self.env['hr.attendance.auto_check']
        return self.env['hr.attendance.auto_check'].search([
            ('employee_id', '=', self.employee_id.id),
            ('contract_id', '=', self.contract_id.id),
            ('day_period', '=', self.day_period),
        ])

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for this in self:
            if not this.employee_id:
                this.contract_id = False
            else:
                contract_ids = this.employee_id.contract_ids.filtered(lambda x: x.state == 'open')
                if len(contract_ids) == 1:
                    this.contract_id = contract_ids

    @api.model
    def create(self, vals):
        # rrhh_asistencias/models/hr_attendance.py
        res = super(HrAttendance, self).create(vals)
        for this in res:
            if self.env['ir.config_parameter'].sudo().get_param('considerar_llegada_anticipada'):
                this.se_procesa_llegada_anticipada = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_llegada_tardia'):
                this.se_procesa_llegada_tardia = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_salida_anticipada'):
                this.se_procesa_salida_anticipada = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_horas_extra_50'):
                this.se_procesa_horas_extra_50 = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_horas_extra_100'):
                this.se_procesa_horas_extra_100 = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_horas_extra_nocturnas'):
                this.se_procesa_horas_extra_nocturnas = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_horas_nocturnas'):
                this.se_procesa_horas_nocturnas = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_plus_hora'):
                this.se_procesa_plus_hora = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_mix_hora'):
                this.se_procesa_mix_hora = True

            auto_checks = this.get_auto_checks()
            for auto_check in auto_checks:
                if auto_check.check_type == 'check_out': this.salida_marcada = this.salida_planeada
                if auto_check.check_type == 'check_in': this.salida_marcada = this.entrada_planeada

        return res

    def get_asistencia_fuera_de_planeado_feriado(self):
        # rrhh_asistencias/models/hr_attendance.py
        for this in self:
            asistencia_fuera_de_planeado = False
            asistencia_feriado = False
            if not (this.entrada_planeada or this.salida_planeada):
                asistencia_fuera_de_planeado = True
            if self.env['calendario.feriado'].check_feriado(this.date, discriminar_domingo=True):
                asistencia_feriado = True
            this.asistencia_fuera_de_planeado = asistencia_fuera_de_planeado
            this.asistencia_feriado = asistencia_feriado

    @api.onchange('date', 'employee_id')
    def get_entrada_salida_planeada(self):
        # rrhh_asistencias/models/hr_attendance.py
        for this in self:
            entrada_planeada = False
            salida_planeada = False
            day_period = False
            resource_calendar_id = False
            if this.employee_id and this.date:
                day_period = 'morning'
                marcaciones_mismo_dia = self.search([
                    ('employee_id', '=', this.employee_id.id),
                    ('contract_id', '=', this.contract_id.id),
                    ('date', '=', this.date),
                    ('entrada_marcada', '<', this.entrada_marcada),
                ]).filtered(lambda marcacion: marcacion != this)
                if marcaciones_mismo_dia:
                    day_period = 'afternoon'
                entrada_planeada = this.contract_id.get_entrada_planeada(this.date, day_period)
                salida_planeada = this.contract_id.get_salida_planeada(this.date, day_period)
                day_period = this.contract_id.get_turno_planeado(this.date, day_period)
                resource_calendar_id = this.contract_id.get_resource_calendar_id_fecha(this.date)
            this.entrada_planeada = entrada_planeada
            this.salida_planeada = salida_planeada
            this.day_period = day_period
            this.resource_calendar_id = resource_calendar_id

    def get_full_check_in_out(self):
        # rrhh_asistencias/models/hr_attendance.py
        for this in self:
            this.full_check_in = False
            this.full_check_out = False
            if this.entrada_marcada:
                this.full_check_in = datetime.datetime.strptime(
                    str(this.date) + ' ' +
                    str(int(this.entrada_marcada)).rjust(2, '0') + ':' +
                    str(int(this.entrada_marcada % 1 * 60)).rjust(2, '0'),
                    '%Y-%m-%d %H:%M'
                )
            if this.salida_marcada:
                this.full_check_out = datetime.datetime.strptime(
                    str(this.date) + ' ' +
                    str(int(this.salida_marcada)).rjust(2, '0') + ':' +
                    str(int(this.salida_marcada % 1 * 60)).rjust(2, '0'),
                    '%Y-%m-%d %H:%M'
                )

    @api.onchange('entrada_marcada', 'salida_marcada', 'entrada_planeada', 'salida_planeada')
    def _get_llegada_anticipada_tardia_extra(self):
        # rrhh_asistencias/models/hr_attendance.py
        for this in self:
            in_plus, out_plus = 0, 0
            horas_extra_50 = 0
            horas_extra_100 = 0
            horas_extra_nocturnas = 0
            horas_nocturnas = 0
            llegada_anticipada = 0
            llegada_tardia = 0
            salida_anticipada = 0

            total_plus_horario = 0
            es_plus_horario = False
            total_mix_horario = 0
            es_mix_horario = False

            if this.asistencia_feriado or (this.asistencia_fuera_de_planeado and this.date and this.date.weekday() == 6):
                horas_extra_100 += this.salida_marcada - this.entrada_marcada
                if this.salida_marcada > 20:
                    horas_nocturnas += this.salida_marcada - max(20, this.entrada_marcada)
                if this.entrada_marcada < 6:
                    horas_nocturnas += min(6, this.salida_marcada) - this.entrada_marcada
            elif this.asistencia_fuera_de_planeado:
                horas_extra_50 = (this.salida_marcada if this.salida_marcada < 20 else 20) - this.entrada_marcada if this.entrada_marcada < 20 else 0
                if this.salida_marcada < 20:
                    horas_extra_100 = 0
                else:
                    horas_extra_100 = this.salida_marcada - (20 if this.entrada_marcada < 20 else this.entrada_marcada)
                if this.salida_marcada > 20:
                    horas_nocturnas += this.salida_marcada - max(20, this.entrada_marcada)
                if this.entrada_marcada < 6:
                    horas_nocturnas += min(6, this.salida_marcada) - this.entrada_marcada
            else:
                if this.entrada_marcada and this.entrada_planeada and (this.entrada_marcada != this.entrada_planeada):
                    if this.entrada_marcada < this.entrada_planeada:
                        llegada_anticipada = (this.entrada_planeada - this.entrada_marcada)
                        llegada_tardia = 0
                    else:
                        llegada_anticipada = 0
                        llegada_tardia = this.entrada_marcada - this.entrada_planeada
                if this.salida_marcada and (this.salida_marcada != this.salida_planeada):
                    if this.salida_marcada > this.salida_planeada:
                        horas_extra_50 = (this.salida_marcada if this.salida_marcada < 20 else 20) - this.salida_planeada if this.salida_planeada < 20 else 0
                        if this.salida_planeada < 20 and this.salida_planeada > 6:
                            horas_extra_nocturnas = this.salida_marcada - 20 if this.salida_marcada > 20 else 0
                        elif this.salida_planeada < 6:
                            horas_extra_nocturnas = (this.salida_marcada if this.salida_marcada < 6 else 6) - this.salida_planeada
                            if this.salida_marcada > 6:
                                horas_extra_50 = this.salida_marcada - 6
                            else:
                                horas_extra_50 = 0
                        else:
                            horas_extra_nocturnas = this.salida_marcada - this.salida_planeada if this.salida_marcada > 20 else 0
                    else:
                        horas_extra_50 = 0
                        horas_extra_nocturnas = 0
                        salida_anticipada = this.salida_planeada - this.salida_marcada

            if self.env['ir.config_parameter'].sudo().get_param('considerar_plus_hora'):
                fin_plus = float(self.env['ir.config_parameter'].sudo().get_param('fin_plus'))
                inicio_plus = float(self.env['ir.config_parameter'].sudo().get_param('inicio_plus'))
                if fin_plus < inicio_plus:
                    if this.entrada_marcada < this.salida_marcada:
                        if this.salida_marcada <= fin_plus and this.entrada_marcada < inicio_plus:
                            this.total_plus_horario = 1.0
                            this.es_plus_horario = True
                    if this.entrada_marcada > this.salida_marcada:
                        if this.salida_marcada <= fin_plus and this.entrada_marcada >= inicio_plus:
                            this.total_plus_horario = 1.0
                            this.es_plus_horario = True
                else:
                    if this.entrada_marcada < this.salida_marcada:
                        if this.salida_marcada <= fin_plus and this.entrada_marcada >= inicio_plus:
                            this.total_plus_horario = 1.0
                            this.es_plus_horario = True

            if self.env['ir.config_parameter'].sudo().get_param('considerar_mix_hora'):
                fin_mix = float(self.env['ir.config_parameter'].sudo().get_param('fin_mix'))
                inicio_mix = float(self.env['ir.config_parameter'].sudo().get_param('inicio_mix'))
                if fin_mix < inicio_mix:
                    if this.entrada_marcada < this.salida_marcada:
                        if this.salida_marcada <= fin_mix and this.entrada_marcada < inicio_mix:
                            total_mix_horario = 1.0
                            es_mix_horario = True
                    if this.entrada_marcada > this.salida_marcada:
                        if this.salida_marcada <= fin_mix and this.entrada_marcada >= inicio_mix:
                            total_mix_horario = 1.0
                            es_mix_horario = True
                else:
                    if this.entrada_marcada < this.salida_marcada:
                        if this.salida_marcada <= fin_mix and this.entrada_marcada >= inicio_mix:
                            total_mix_horario = 1.0
                            es_mix_horario = True
            if self.env['ir.config_parameter'].sudo().get_param('considerar_horas_nocturnas_en_planeado'):
                if not this.asistencia_fuera_de_planeado and not this.asistencia_feriado:
                    horas_nocturnas = 0
                    if this.salida_planeada > 20:
                        horas_nocturnas += min(this.salida_marcada, this.salida_planeada) - max(20, this.entrada_marcada)
                    if this.entrada_planeada < 6:
                        horas_nocturnas += min(6, this.salida_marcada, this.salida_planeada) - max(this.entrada_marcada, this.entrada_planeada)

            if this.contract_id.company_id.hr_attendance_overtime:
                tolerancia_llegada_tardia = this.contract_id.company_id.overtime_employee_threshold
                tolerancia_horas_extra = this.contract_id.company_id.overtime_company_threshold
                tolerancia_salida_anticipada = this.contract_id.company_id.overtime_employee_threshold_early_leaves
                if tolerancia_llegada_tardia and llegada_tardia:
                    llegada_tardia_minutos = round(llegada_tardia * 60)
                    if tolerancia_llegada_tardia >= llegada_tardia_minutos:
                        llegada_tardia = 0
                if tolerancia_horas_extra:
                    if (horas_extra_50 or horas_extra_nocturnas):
                        horas_extra_50_minutos = round(horas_extra_50 * 60)
                        horas_extra_nocturnas_minutos = round(horas_extra_nocturnas * 60)
                        if horas_extra_50_minutos:
                            if tolerancia_horas_extra >= horas_extra_50_minutos:
                                horas_extra_50 = 0
                        elif horas_extra_nocturnas_minutos:
                            if tolerancia_horas_extra >= horas_extra_nocturnas_minutos:
                                horas_extra_nocturnas = 0
                    if llegada_anticipada:
                        llegada_anticipada_minutos = round(llegada_anticipada * 60)
                        if tolerancia_horas_extra >= llegada_anticipada_minutos:
                            llegada_anticipada = 0
                if tolerancia_salida_anticipada and salida_anticipada:
                    salida_anticipada_minutos = round(salida_anticipada * 60)
                    if tolerancia_salida_anticipada >= salida_anticipada_minutos:
                        salida_anticipada = 0

            this.horas_extra_50 = horas_extra_50
            this.horas_extra_100 = horas_extra_100
            this.horas_extra_nocturnas = horas_extra_nocturnas
            this.horas_nocturnas = horas_nocturnas
            this.llegada_anticipada = llegada_anticipada
            this.llegada_tardia = llegada_tardia
            this.salida_anticipada = salida_anticipada

            this.total_plus_horario = total_plus_horario
            this.es_plus_horario = es_plus_horario
            this.total_mix_horario = total_mix_horario
            this.es_mix_horario = es_mix_horario

    @api.depends('entrada_marcada', 'salida_marcada')
    def _compute_worked_hours(self):
        # rrhh_asistencias/models/hr_attendance.py
        for this in self:
            if this.get_auto_checks():
                if this.entrada_marcada > this.salida_marcada:
                    aux = this.salida_marcada
                    this.salida_marcada = this.entrada_marcada
                    this.entrada_marcada = aux
            if this.salida_marcada and this.entrada_marcada:
                this.worked_hours = this.salida_marcada - this.entrada_marcada
            else:
                this.worked_hours = False

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        # rrhh_asistencias/models/hr_attendance.py
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(_(
                    "Cannot create new attendance record for 21 %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                                                     'empl_name': attendance.employee_id.name,
                                                     'datetime': format_datetime(self.env, attendance.check_in,
                                                                                 dt_format=False),
                                                 })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                '''if no_check_out_attendances:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for 22 %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                        'empl_name': attendance.employee_id.name,
                        'datetime': format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False),
                    })'''
            else:
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
                last_attendance_before_check_out = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_in', '<', attendance.check_out),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                    raise exceptions.ValidationError(_(
                        "Cannot create new attendance record for 23 %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                                                         'empl_name': attendance.employee_id.name,
                                                         'datetime': format_datetime(self.env,
                                                                                     last_attendance_before_check_out.check_in,
                                                                                     dt_format=False),
                                                     })

    def _update_overtime(self, employee_attendance_dates=None):
        return


class ResUsers(models.Model):
    _inherit = 'res.users'

    last_check_in = fields.Datetime(related='employee_id.last_attendance_id.full_check_in')
    last_check_out = fields.Datetime(related='employee_id.last_attendance_id.full_check_out')
