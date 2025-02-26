# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from collections import defaultdict
import datetime


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    contract_id = fields.Many2one('hr.contract')
    request_hour_from = fields.Float()
    request_hour_to = fields.Float()

    @api.constrains('date_from', 'date_to')
    def _check_contracts(self):
        # rrhh_payroll/models/hr_leave.py
        return

    def _create_resource_leave(self):
        # rrhh_payroll/models/hr_leave.py
        """
        Add a resource leave in calendars of contracts running at the same period.
        This is needed in order to compute the correct number of hours/days of the leave
        according to the contract's calender.
        """
        # resource_leaves = super(HrLeave, self)._create_resource_leave()
        vals_list = [{
            'name': leave.name,
            'date_from': leave.date_from,
            'holiday_id': leave.id,
            'date_to': leave.date_to,
            'resource_id': leave.employee_id.resource_id.id,
            'calendar_id': leave.employee_id.resource_calendar_id.id,
            'time_type': leave.holiday_status_id.time_type,
        } for leave in self]
        resource_leaves = self.env['resource.calendar.leaves'].sudo().create(vals_list)
        for resource_leave in resource_leaves:
            resource_leave.work_entry_type_id = resource_leave.holiday_id.holiday_status_id.work_entry_type_id.id

        resource_leave_values = []

        for leave in self.filtered(lambda l: l.employee_id):

            # contract = leave.employee_id.sudo()._get_contracts(leave.date_from, leave.date_to, states=['open'])
            contract = leave.contract_id
            if contract and contract.resource_calendar_id != leave.employee_id.resource_calendar_id:
                resource_leave_values += [{
                    'name': leave.name,
                    'holiday_id': leave.id,
                    'resource_id': leave.employee_id.resource_id.id,
                    'work_entry_type_id': leave.holiday_status_id.work_entry_type_id.id,
                    'time_type': leave.holiday_status_id.time_type,
                    'date_from': max(leave.date_from,
                                     datetime.datetime.combine(contract.date_start, datetime.datetime.min.time())),
                    'date_to': min(leave.date_to, datetime.datetime.combine(contract.date_end or datetime.date.max,
                                                                            datetime.datetime.max.time())),
                    'calendar_id': contract.resource_calendar_id.id,
                }]

        return resource_leaves | self.env['resource.calendar.leaves'].create(resource_leave_values)

    def _cancel_work_entry_conflict(self):
        # rrhh_payroll/models/hr_leave.py
        """
        Creates a leave work entry for each hr.leave in self.
        Check overlapping work entries with self.
        Work entries completely included in a leave are archived.
        e.g.:
            |----- work entry ----|---- work entry ----|
                |------------------- hr.leave ---------------|
                                    ||
                                    vv
            |----* work entry ****|
                |************ work entry leave --------------|
        """
        if not self:
            return

        # 1. Create a work entry for each leave
        work_entries_vals_list = []
        for leave in self:
            # contracts = leave.employee_id.sudo()._get_contracts(leave.date_from, leave.date_to, states=['open', 'close'])
            contracts = leave.contract_id
            for contract in contracts:
                # Generate only if it has aleady been generated
                work_entries_vals_list += contracts._get_work_entries_values(leave.date_from, leave.date_to,
                                                                             force_create=True)

        for work_entries_vals in work_entries_vals_list:
            if work_entries_vals['date_start'] > work_entries_vals['date_stop']:
                aux = work_entries_vals['date_start']
                work_entries_vals['date_start'] = work_entries_vals['date_stop']
                work_entries_vals['date_stop'] = aux

        new_leave_work_entries = self.env['hr.work.entry'].create(work_entries_vals_list)

        if new_leave_work_entries:
            # 2. Fetch overlapping work entries, grouped by employees
            start = min(self.mapped('date_from'), default=False)
            stop = max(self.mapped('date_to'), default=False)
            work_entry_groups = self.env['hr.work.entry'].read_group([
                ('date_start', '<', stop),
                ('date_stop', '>', start),
                ('employee_id', 'in', self.employee_id.ids),
            ], ['work_entry_ids:array_agg(id)', 'employee_id'], ['employee_id', 'date_start', 'date_stop'], lazy=False)
            work_entries_by_employee = defaultdict(lambda: self.env['hr.work.entry'])
            for group in work_entry_groups:
                employee_id = group.get('employee_id')[0]
                work_entries_by_employee[employee_id] |= self.env['hr.work.entry'].browse(group.get('work_entry_ids'))

            # 3. Archive work entries included in leaves
            included = self.env['hr.work.entry']
            overlappping = self.env['hr.work.entry']
            for work_entries in work_entries_by_employee.values():
                # Work entries for this employee
                new_employee_work_entries = work_entries & new_leave_work_entries
                previous_employee_work_entries = work_entries - new_leave_work_entries

                # Build intervals from work entries
                leave_intervals = new_employee_work_entries._to_intervals()
                conflicts_intervals = previous_employee_work_entries._to_intervals()

                # Compute intervals completely outside any leave
                # Intervals are outside, but associated records are overlapping.
                outside_intervals = conflicts_intervals - leave_intervals

                overlappping |= self.env['hr.work.entry']._from_intervals(outside_intervals)
                included |= previous_employee_work_entries - overlappping
            overlappping.write({'leave_id': False})
            included.write({'active': False})

    def action_refuse(self):
        # rrhh_payroll/models/hr_leave.py
        work_entries = self.env['hr.work.entry'].sudo().search([('leave_id', 'in', self.ids)])
        r = super(HrLeave, self).action_refuse()
        work_entries.write({'active': False})
        return r

    @api.onchange('date_from', 'date_to', 'employee_id', 'holiday_status_id')
    def _onchange_leave_dates(self):
        # rrhh_payroll/models/hr_leave.py
        for this in self:
            this.number_of_days = this.get_number_of_days()

    def get_number_of_days(self):
        # rrhh_payroll/models/hr_leave.py
        number_of_days = 0
        ausencia_dias_corridos = self.holiday_status_id.ausencia_dias_corridos
        if self.date_from and self.date_to and self.date_from <= self.date_to:
            date_aux = self.date_from
            allowed_days = self.contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek')
            while date_aux <= self.date_to:
                if str(date_aux.weekday()) in allowed_days or ausencia_dias_corridos:
                    number_of_days += self.env['calendario.feriado'].contar_dias_laborales(date_aux, date_aux, ausencia_dias_corridos, allowed_days)
                date_aux += datetime.timedelta(days=1)
        return number_of_days

    @api.constrains('date_from', 'date_to', 'state', 'employee_id')
    def _check_date(self):
        # rrhh_payroll/models/hr_leave.py
        return

    def write(self, vals):
        # rrhh_payroll/models/hr_leave.py
        result = super(HrLeave, self).write(vals)
        for this in self:
            if not (this.request_unit_half or this.request_unit_hours):
                number_of_days = this.get_number_of_days()
                if this.number_of_days != number_of_days:
                    this.number_of_days = number_of_days
        return result
