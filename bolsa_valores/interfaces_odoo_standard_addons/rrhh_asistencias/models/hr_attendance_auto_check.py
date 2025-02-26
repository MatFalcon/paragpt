from odoo import fields, api, models, exceptions, _


class HrAttendanceAutoCheck(models.Model):
    _name = 'hr.attendance.auto_check'
    _sql_constraints = [
        ('auto_check_unique', 'unique(contract_id,check_type,day_period,active)',
         'Ya existe una regla de marcaciones automáticas para este empleado con los mismos valores')
    ]
    _description = 'Modelo para definir las marcaciones automáticas para los empleados, destinado a turnos que empiezan en un día y terminan en otro'

    employee_id = fields.Many2one(comodel_name='hr.employee', string='Empleado', required=True)
    contract_id = fields.Many2one(comodel_name='hr.contract', string='Contrato', required=True)

    check_type = fields.Selection(string='Tipo de Marcación', selection=[('check_in', 'Entrada'), ('check_out', 'Salida'), ], required=True)
    day_period = fields.Selection(string='Periodo del día', selection=[('morning', 'Mañana'), ('afternoon', 'Tarde'), ], default='morning', required=True)

    active = fields.Boolean(string='Activo', default=True)

    def toggle_active(self):
        for this in self:
            this.active = not this.active
