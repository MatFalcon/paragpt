from odoo import fields, api, models, exceptions, _


class HrAttendanceCalendar(models.Model):
    _name = 'hr.attendance.calendar'
    _description = 'Planeamiento de Asistencias'
    _order = 'applied_on, contract_id, department_id, sequence desc, date_from desc, date_to desc'

    applied_on = fields.Selection([
        ('employee', 'Empleado'),
        ('department', 'Departamento'),
    ], string='Aplicar sobre', default='employee', required=True)
    employee_id = fields.Many2one('hr.employee', string='Empleado', copy=False)
    contract_id = fields.Many2one('hr.contract', string='Contrato', copy=False)
    department_id = fields.Many2one('hr.department', string='Departamento', copy=False)
    company_id = fields.Many2one('res.company', string='Compañía', compute='_set_company_id', store=True)
    resource_calendar_id = fields.Many2one('resource.calendar', string='Horario', required=True)
    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)
    attendance_calendar_conflict = fields.Boolean(compute='check_attendance_calendar_conflict')
    sequence = fields.Integer(string='Prioridad', default=0,
                              help='Cuando existe más de un planeamiento con el mismo departamento o el mismo contrato, se debe de establecer la prioridad de cada uno de ellos')

    @api.depends('contract_id.company_id')
    def _set_company_id(self):
        for this in self:
            this.company_id = this.contract_id.company_id

    @api.depends('applied_on', 'employee_id', 'contract_id', 'department_id', 'date_from', 'date_to')
    def check_attendance_calendar_conflict(self):
        # rrhh_asistencias/models/hr_attendance_calendar.py
        for this in self:
            attendance_calendar_conflict = False
            domain = [
                '|',
                '|',
                '&',
                ('date_from', '<=', this.date_from),
                ('date_to', '>=', this.date_from),
                '&',
                ('date_from', '<=', this.date_to),
                ('date_to', '>=', this.date_to),
                '&',
                ('date_from', '>=', this.date_from),
                ('date_to', '<=', this.date_to),
            ]
            if this.applied_on == 'employee' and this.contract_id:
                domain += [
                    ('applied_on', '=', 'employee'),
                    ('contract_id', '=', this.contract_id.id),
                ]
            elif this.applied_on == 'department' and this.department_id:
                domain += [
                    ('applied_on', '=', 'department'),
                    ('department_id', '=', this.department_id.id),
                ]
            if self.search(domain).filtered(lambda x: x != this):
                attendance_calendar_conflict = True
            this.attendance_calendar_conflict = attendance_calendar_conflict

    # def check_duplicates(self):
    #     # rrhh_asistencias/models/hr_attendance_calendar.py
    #     error = ''
    #     for this in self:
    #         domain = [
    #             ('id', '!=', this.id),
    #             '|',
    #             '|',
    #             '&',
    #             ('date_from', '<=', this.date_from),
    #             ('date_to', '>=', this.date_from),
    #             '&',
    #             ('date_from', '<=', this.date_to),
    #             ('date_to', '>=', this.date_to),
    #             '&',
    #             ('date_from', '>=', this.date_from),
    #             ('date_to', '<=', this.date_to),
    #         ]
    #         if this.applied_on == 'employee' and this.contract_id:
    #             domain += [
    #                 ('applied_on', '=', 'employee'),
    #                 ('contract_id', '=', this.contract_id.id),
    #             ]
    #             if self.search(domain):
    #                 error = 'Ya existe un Planeamiento de Asistencias para el contrato ' + this.contract_id.name + ' que afecta la fecha solicitada'
    #         elif this.applied_on == 'department' and this.department_id:
    #             domain += [
    #                 ('applied_on', '=', 'department'),
    #                 ('department_id', '=', this.department_id.id),
    #             ]
    #             if self.search(domain):
    #                 error = 'Ya existe un Planeamiento de Asistencias para el departamento ' + this.department_id.name + ' que afecta la fecha solicitada'
    #         if error: raise exceptions.ValidationError(error)

    # @api.model_create_multi
    # @api.returns('self', lambda value: value.id)
    # def create(self, vals_list):
    #     # rrhh_asistencias/models/hr_attendance_calendar.py
    #     r = super(HrAttendanceCalendar, self).create(vals_list)
    #     r.check_duplicates()
    #     return r
    #
    # def write(self, vals):
    #     # rrhh_asistencias/models/hr_attendance_calendar.py
    #     r = super(HrAttendanceCalendar, self).write(vals)
    #     self.check_duplicates()
    #     return r
