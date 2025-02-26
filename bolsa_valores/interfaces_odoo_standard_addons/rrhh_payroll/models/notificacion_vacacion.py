# -*- coding: utf-8 -*-
import odoo, datetime
from odoo import models, fields, api, exceptions, _
from odoo.addons.reportes_ministerio_trabajo_py.models import amount_to_text_spanish


def get_mes(mes):
    switcher = [
        'ENERO',
        'FEBRERO',
        'MARZO',
        'ABRIL',
        'MAYO',
        'JUNIO',
        'JULIO',
        'AGOSTO',
        'SETIEMBRE',
        'OCTUBRE',
        'NOVIEMBRE',
        'DICIEMBRE']
    return switcher[mes - 1]


class NotificacionVacacion(models.Model):
    _name = 'notificacion.vacacion'
    _description = 'Notificación de vacaciones para los empleados'

    employee_id = fields.Many2one('hr.employee', string='Empleado', required=True)
    contract_id = fields.Many2one('hr.contract', string='Contrato', required=True)
    company_id = fields.Many2one('res.company', string='Compañia', related='contract_id.company_id')
    dias_vacaciones = fields.Integer('Días de vacaciones', required=True)
    fecha_notificacion_vacaciones = fields.Date(string='Notificación de Vacaciones', compute='_get_fecha_notificacion_vacaciones')
    fecha_pago_vacaciones = fields.Date(string='Pago de Vacaciones', compute='_get_fecha_pago_vacaciones')
    fecha_inicio_vacaciones = fields.Date(string='Inicio de Vacaciones', required=True)
    fecha_fin_vacaciones = fields.Date(string='Fin de Vacaciones', required=True)
    fecha_reincorporacion_vacaciones = fields.Date(string='Reincorporación de Vacaciones', compute='_get_fecha_reincorporacion_vacaciones')
    state = fields.Selection(selection=[('hold', 'Pendiente'), ('done', 'Procesado')], string='Estado', default='hold')
    payslip_id = fields.Many2one('hr.payslip', string='Nómina')
    currency_id = fields.Many2one(related='contract_id.currency_id')
    payslip_net_amount = fields.Float(string='Monto', compute='get_payslip_net_amount')
    leave_id = fields.Many2one('hr.leave', string='Ausencia')
    periodo_usufructuado = fields.Char(string='Periodio Usufructuado')

    def get_payslip_net_amount(self):
        # rrhh_payroll/models/notificacion_vacacion.py
        for this in self:
            if this.payslip_id and this.payslip_id.state == 'done':
                this.payslip_net_amount = sum(this.payslip_id.line_ids.filtered(lambda x: x.code == 'NET').mapped('total'))
            else:
                this.payslip_net_amount = 0

    def get_mes(self, mes):
        # rrhh_payroll/models/notificacion_vacacion.py
        return get_mes(mes)

    def get_dia(self, weekday):
        # rrhh_payroll/models/notificacion_vacacion.py
        return ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][weekday]

    def numero_a_letras(self, monto):
        # rrhh_payroll/models/notificacion_vacacion.py
        return amount_to_text_spanish.to_word(monto)

    def obtener_vacaciones_antiguedad(self, today, date_start):
        # rrhh_payroll/models/notificacion_vacacion.py
        dias_vacaciones = 0
        antiguedad_vacaciones = self.env['antiguedad.vacaciones'].search([], order='antiguedad_dias')
        for i in antiguedad_vacaciones:
            if (today - date_start).days >= i.antiguedad_dias:
                dias_vacaciones = i.dias_vacaciones
            else:
                break
        return dias_vacaciones

    @api.depends('fecha_inicio_vacaciones')
    @api.onchange('fecha_inicio_vacaciones')
    def _get_fecha_notificacion_vacaciones(self):
        for this in self:
            fecha_notificacion_vacaciones = False
            if this.fecha_inicio_vacaciones:
                fecha_notificacion_vacaciones = this.fecha_inicio_vacaciones - datetime.timedelta(days=15)
                while self.env['calendario.feriado'].check_feriado(fecha_notificacion_vacaciones) or \
                        str(fecha_notificacion_vacaciones.weekday()) not in self.contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek'):
                    fecha_notificacion_vacaciones -= datetime.timedelta(days=1)
            this.fecha_notificacion_vacaciones = fecha_notificacion_vacaciones

    @api.depends('fecha_inicio_vacaciones')
    @api.onchange('fecha_inicio_vacaciones')
    def _get_fecha_pago_vacaciones(self):
        for this in self:
            fecha_pago_vacaciones = False
            if this.fecha_inicio_vacaciones:
                fecha_pago_vacaciones = this.fecha_inicio_vacaciones - datetime.timedelta(days=1)
                while self.env['calendario.feriado'].check_feriado(fecha_pago_vacaciones) or \
                        str(fecha_pago_vacaciones.weekday()) not in self.contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek'):
                    fecha_pago_vacaciones -= datetime.timedelta(days=1)
            this.fecha_pago_vacaciones = fecha_pago_vacaciones

    @api.depends('fecha_fin_vacaciones')
    @api.onchange('fecha_fin_vacaciones')
    def _get_fecha_reincorporacion_vacaciones(self):
        for this in self:
            fecha_reincorporacion_vacaciones = False
            if this.fecha_fin_vacaciones:
                fecha_reincorporacion_vacaciones = this.fecha_fin_vacaciones + datetime.timedelta(days=1)
                while this.env['calendario.feriado'].check_feriado(fecha_reincorporacion_vacaciones) or \
                        str(fecha_reincorporacion_vacaciones.weekday()) not in self.contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek'):
                    fecha_reincorporacion_vacaciones += datetime.timedelta(days=1)
            this.fecha_reincorporacion_vacaciones = fecha_reincorporacion_vacaciones

    def obtener_contratos_a_notificar(self, year=False, month=False):
        # rrhh_payroll/models/notificacion_vacacion.py
        if year and month:
            today = datetime.datetime.strptime('01/' + str(month) + '/' + str(year), '%d/%m/%Y').date()
        else:
            today = fields.Date.today()
        contracts = self.env['hr.contract'].search([('state', 'in', ['open'])])
        # contracts = contracts.filtered(lambda x: (x.date_start - datetime.timedelta(days=15)).month == today.month)
        for contract in contracts:
            current_notification_date = (contract.date_start.replace(year=today.year) - datetime.timedelta(days=15))
            current_aniversario_date = (contract.date_start.replace(year=today.year))
            domain = [('employee_id', '=', contract.employee_id.id), ('contract_id', '=', contract.id)]
            if not self.search(domain + [('state', '=', 'hold')]) and current_aniversario_date >= today:
                dias_vacaciones = self.obtener_vacaciones_antiguedad(current_aniversario_date, contract.date_start)
                # if contract.wage_type == 'daily':
                #     dias_vacaciones = round(dias_vacaciones / 30 * contract.dias_a_trabajar)
                # inicio_vacaciones_t = contract.date_start.replace(year=today.year)
                inicio_vacaciones_t = current_aniversario_date
                if inicio_vacaciones_t.weekday() == 0 and inicio_vacaciones_t.day <= 7:
                    inicio_vacaciones_t = inicio_vacaciones_t  # FIXME
                # else:
                #     current_month = inicio_vacaciones_t.month
                #     while inicio_vacaciones_t.month == current_month:
                #         inicio_vacaciones_t += datetime.timedelta(days=1)
                while not (inicio_vacaciones_t.weekday() == 0 and not self.env['calendario.feriado'].check_feriado(inicio_vacaciones_t)):
                    inicio_vacaciones_t += datetime.timedelta(days=1)
                allowed_days = contract.resource_calendar_id.attendance_ids.mapped('dayofweek')
                fin_vacaciones_t = self.env['calendario.feriado'].sumar_dias_laborales(
                    inicio_vacaciones_t,
                    dias_vacaciones,
                    allowed_days
                )
                mes_a_procesar = today.month + 1 if today.month < 12 else 1
                if inicio_vacaciones_t.month == mes_a_procesar and not self.search(domain + [('fecha_inicio_vacaciones', '=', inicio_vacaciones_t)]):
                    self.create({
                        'employee_id': contract.employee_id.id,
                        'contract_id': contract.id,
                        'dias_vacaciones': dias_vacaciones,
                        'fecha_inicio_vacaciones': inicio_vacaciones_t,
                        'fecha_fin_vacaciones': fin_vacaciones_t,
                    })

    def generar_nominas(self):
        # rrhh_payroll/models/notificacion_vacacion.py
        for this in self.filtered(lambda x: not x.leave_id):
            name_lote = 'Vacaciones ' + get_mes(this.fecha_inicio_vacaciones.month) + ' ' + str(this.fecha_inicio_vacaciones.year)
            payslip_run_id = self.env['hr.payslip.run'].search([
                ('name', '=', name_lote),
                ('company_id', '=', this.contract_id.company_id.id),
            ])
            if not payslip_run_id:
                payslip_run_id = payslip_run_id.create({
                    'company_id': this.contract_id.company_id.id,
                    'name': name_lote,
                    'date_start': this.fecha_inicio_vacaciones.replace(day=1),
                    'date_end': this.fecha_inicio_vacaciones.replace(day=fields.Date().end_of(this.fecha_inicio_vacaciones, 'month').day),
                })

            this.payslip_id = this.env['hr.payslip'].create({
                'name': 'Nómina ' + this.contract_id.employee_id.name + ' ' + this.contract_id.company_id.payroll_structure_default_vacacion.name + ' ' + str(
                    this.fecha_inicio_vacaciones.year),
                'company_id': this.contract_id.company_id.id,
                'payslip_run_id': payslip_run_id.id,
                'employee_id': this.employee_id.id,
                'contract_id': this.contract_id.id,
                'date_from': this.fecha_inicio_vacaciones,
                'date_to': this.fecha_fin_vacaciones,
                'struct_id': this.contract_id.company_id.payroll_structure_default_vacacion.id,
            }).id
            this.leave_id = this.env['hr.leave'].create({
                'holiday_status_id': self.env.ref('reportes_ministerio_trabajo_py.tipo_ausencia_vacaciones').id,
                'holiday_type': 'employee',
                'employee_id': this.employee_id.id,
                'contract_id': this.contract_id.id,
                'request_date_from': this.fecha_inicio_vacaciones,
                'request_date_to': this.fecha_fin_vacaciones,
                'date_from': str(this.fecha_inicio_vacaciones) + ' 12:00:00',
                'date_to': str(this.fecha_fin_vacaciones) + ' 12:00:00',
            })
            this.leave_id._onchange_leave_dates()
            this.leave_id.action_approve()
            this.payslip_id.reset_worked_days()
            this.payslip_id.compute_sheet()
            this.payslip_id.action_payslip_done()
            this.write({'state': 'done'})

    def cancelar_notificacion(self):
        # rrhh_payroll/models/notificacion_vacacion.py
        for this in self:
            if this.payslip_id.state != 'draft':
                this.payslip_id.action_payslip_cancel()
                this.payslip_id.action_payslip_draft()
                this.payslip_id.unlink()
            if this.leave_id.state != 'draft':
                this.leave_id.action_refuse()
                this.leave_id.action_draft()
                this.leave_id.unlink()
        self.write({'state': 'hold'})

    def unlink(self):
        # rrhh_payroll/models/notificacion_vacacion.py
        if any([x.state == 'done' for x in self]):
            raise exceptions.UserError(
                _('No se puede eliminar una notificación que esté confirmada, primero debe cancelarla'))
        else:
            return super(NotificacionVacacion, self).unlink()
