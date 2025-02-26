# -*- coding: utf-8 -*-
from odoo import api, fields, models, exceptions, _
from datetime import date, datetime, time
import pytz
from odoo.addons.reportes_ministerio_trabajo_py.models import amount_to_text_spanish


class HRContract(models.Model):
    _inherit = 'hr.contract'

    analytic_tag_ids = fields.Many2many("account.analytic.tag", string="Etiquetas analíticas")
    seguro_ips = fields.Boolean('Cuenta con Seguro IPS', default=True)

    structure_id = fields.Many2one('hr.payroll.structure', string='Estructura Salarial', required=True)

    def _get_work_entries_values(self, date_start, date_stop, force_create=False):
        # rrhh_payroll/models/hr_contract
        """
        Generate a work_entries list between date_start and date_stop for one contract.
        :return: list of dictionnary.
        """
        default_work_entry_type = self.structure_type_id.default_work_entry_type_id
        vals_list = []
        if not force_create:
            return vals_list
        for contract in self:
            contract_vals = []
            employee = contract.employee_id
            calendar = contract.resource_calendar_id
            resource = employee.resource_id
            tz = pytz.timezone(calendar.tz)

            attendances = calendar._work_intervals_batch(
                pytz.utc.localize(date_start) if not date_start.tzinfo else date_start,
                pytz.utc.localize(date_stop) if not date_stop.tzinfo else date_stop,
                resources=resource, tz=tz
            )[resource.id]
            # Attendances
            for interval in attendances:
                work_entry_type_id = interval[2].mapped('work_entry_type_id')[:1] or default_work_entry_type
                # All benefits generated here are using datetimes converted from the employee's timezone
                contract_vals += [{
                    'name': "%s: %s" % (work_entry_type_id.name, employee.name),
                    'date_start': interval[0].astimezone(pytz.utc).replace(tzinfo=None),
                    'date_stop': interval[1].astimezone(pytz.utc).replace(tzinfo=None),
                    'work_entry_type_id': work_entry_type_id.id,
                    'employee_id': employee.id,
                    'contract_id': contract.id,
                    'company_id': contract.company_id.id,
                    'state': 'draft',
                }]

            # Leaves
            leaves = self.env['resource.calendar.leaves'].sudo().search([
                ('resource_id', 'in', [False, resource.id]),
                ('calendar_id', '=', calendar.id),
                ('date_from', '<', date_stop),
                ('date_to', '>', date_start)
            ])

            for leave in leaves:
                start = max(leave.date_from, datetime.combine(contract.date_start, datetime.min.time()))
                end = min(leave.date_to, datetime.combine(contract.date_end or date.max, datetime.max.time()))
                if leave.holiday_id:
                    work_entry_type = leave.holiday_id.holiday_status_id.work_entry_type_id
                else:
                    work_entry_type = leave.mapped('work_entry_type_id')
                contract_vals += [{
                    'name': "%s%s" % (work_entry_type.name + ": " if work_entry_type else "", employee.name),
                    'date_start': start,
                    'date_stop': end,
                    'work_entry_type_id': work_entry_type.id,
                    'employee_id': employee.id,
                    'leave_id': leave.holiday_id and leave.holiday_id.id,
                    'company_id': contract.company_id.id,
                    'state': 'draft',
                    'contract_id': contract.id,
                }]

            # If we generate work_entries which exceeds date_start or date_stop, we change boundaries on contract
            if contract_vals:
                date_stop_max = max([x['date_stop'] for x in contract_vals])
                if date_stop_max > contract.date_generated_to:
                    contract.date_generated_to = date_stop_max

                date_start_min = min([x['date_start'] for x in contract_vals])
                if date_start_min < contract.date_generated_from:
                    contract.date_generated_from = date_start_min

            vals_list += contract_vals

        return vals_list

    def check_notificaciones_vacaciones(self):
        # rrhh_payroll/models/hr_contract.py
        fecha_hoy = fields.date.today()
        for this in self:
            if self.env['notificacion.vacacion'].search([
                ('contract_id', '=', this.id),
                ('state', '=', 'done'),
            ]).filtered(lambda notificacion_vacacion:
                        notificacion_vacacion.fecha_inicio_vacaciones >= fecha_hoy.replace(day=1) or
                        notificacion_vacacion.fecha_fin_vacaciones >= fecha_hoy.replace(day=1)
                        ):
                raise exceptions.ValidationError(_('Existen notificaciones de vacaciones para este contrato confirmadas en este mes o en los siguientes.'
                                                   + 'Modificar los salarios puede producir inconsistencias en los montos, debe cancelar dichas notificaciones para poder continuar.'))

    def write(self, vals):
        # rrhh_payroll/models/hr_contract.py
        if any(key in vals for key in ['check_sueldo_minimo', 'check_jornal_minimo', 'salario_minimo_id', 'wage', 'hourly_wage', 'daily_wage']):
            self.check_notificaciones_vacaciones()
        return super(HRContract, self).write(vals)
