from odoo import api, fields, models, exceptions
from odoo.addons.reportes_ministerio_trabajo_py.models import amount_to_text_spanish
#import xlrd, pytz, datetime


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


class HRPayslip(models.Model):
    _inherit = 'hr.payslip'

    mes_correspondiente = fields.Char(compute='_get_mes')
    es_nomina_vacaciones = fields.Boolean(compute='_get_es_nomina_vacaciones')
    legacy_payslip_details = fields.Boolean()

    def compute_sheet(self):
        self.write({'legacy_payslip_details': False})
        return super(HRPayslip, self).compute_sheet()

    def _get_es_nomina_vacaciones(self):
        # rrhh_payroll/models/hr_payslip.py
        for this in self:
            this.es_nomina_vacaciones = True if this.env['notificacion.vacacion'].search(
                [('payslip_id', '=', this.id)]) else False

    def numero_a_letras(self, monto):
        # rrhh_payroll/models/hr_payslip.py
        return amount_to_text_spanish.to_word(monto)

    def _get_mes(self, mes=False):
        # rrhh_payroll/models/hr_payslip.py
        if mes:
            return get_mes(mes)
        for this in self:
            this.mes_correspondiente = get_mes(this.date_from.month)

    # def get_computed_month_wage(self):
    #     self.computed_month_wage = 0
    #     for this in self:
    #         if 'WORK100' in this.mapped('worked_days_line_ids.code'):
    #             payslip_real_wage = this.worked_days_line_ids.filtered(lambda line: line.code == 'WORK100').amount
    #             if this.contract_id.wage_type == 'monthly' or this.contract_id.salario_minimo_id:
    #                 salario = payslip_real_wage
    #             elif this.contract_id.wage_type == 'hourly':
    #                 salario = payslip_real_wage * 8 * 30
    #             else:
    #                 salario = payslip_real_wage * 30
    #             this.computed_month_wage = salario
    #         elif 'DTRAB' in this.mapped('line_ids.code'):
    #             this.computed_month_wage = this.contract_id.computed_daily_wage * 30

    def get_asistencias_totales(self):
        # rrhh_payroll/models/hr_payslip.py
        dias_trabajados = 30
        if self.contract_id.wage_type == 'daily':
            dias_trabajados = self.contract_id.number_of_planned_work_days
        elif self.contract_id.wage_type == 'monthly':
            date_aux = self.date_from
            if self.contract_id and date_aux < self.contract_id.date_start:
                while date_aux <= self.date_to:
                    if date_aux < self.contract_id.date_start:
                        dias_trabajados -= 1
                    date_aux += datetime.timedelta(days=1)

        cant_asistencias = {
            'WORK100': {
                'cant_dias': dias_trabajados,
                'cant_horas': 0,
            },
            'VAC': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'AUS': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'HEX50': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'HEX100': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'HEXNOC': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'HNOC': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'LLA': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'LLT': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'SAA': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'HTP': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
            'HMX': {
                'cant_dias': 0,
                'cant_horas': 0,
            },
        }
        ausencias = self.env['hr.leave'].search([('state', '=', 'validate'), ('contract_id', '=', self.contract_id.id)])
        for codigo_ausencia in list(set(ausencias.mapped('holiday_status_id.code'))):
            if codigo_ausencia not in cant_asistencias.keys():
                cant_asistencias[codigo_ausencia] = {
                    'cant_dias': 0,
                    'cant_horas': 0,
                }
            cant_asistencias[codigo_ausencia]['cant_dias'] = 0
        for ausencia in ausencias:
            if ausencia.request_unit_half or ausencia.request_unit_hours:
                if self.date_from <= ausencia.request_date_from <= self.date_to and not \
                        self.env['calendario.feriado'].check_feriado(ausencia.request_date_from):
                    if ausencia.request_unit_half:
                        cant_asistencias[ausencia.holiday_status_id.code]['cant_dias'] += ausencia.number_of_days_display
                    else:
                        cant_asistencias[ausencia.holiday_status_id.code]['cant_horas'] += ausencia.number_of_hours_display
            else:
                date_aux = ausencia.request_date_from
                while date_aux <= ausencia.request_date_to:
                    if self.date_from <= date_aux <= self.date_to and (
                            ausencia.holiday_status_id.ausencia_dias_corridos or
                            not self.env['calendario.feriado'].check_feriado(date_aux)) and \
                            str(date_aux.weekday()) in self.contract_id.resource_calendar_id.attendance_ids.mapped('dayofweek'):
                        cant_asistencias[ausencia.holiday_status_id.code]['cant_dias'] += 1
                    date_aux += datetime.timedelta(days=1)

        # Paso necesario para evitar problemas con exceso de decimales
        for cant_asistencia in cant_asistencias:
            cant_asistencias[cant_asistencia]['cant_dias'] = round(cant_asistencias[cant_asistencia]['cant_dias'], 2)
            cant_asistencias[cant_asistencia]['cant_horas'] = round(cant_asistencias[cant_asistencia]['cant_horas'], 2)
        return cant_asistencias

    def reset_worked_days(self, recompute=False):
        # rrhh_payroll/models/hr_payslip.py
        r = super(HRPayslip, self).compute_sheet()

        for this in self:
            cant_asistencias = this.get_asistencias_totales()
            this.write({
                'worked_days_line_ids': [(5, 0, 0)]
            })
            tipo_entrada_vacaciones = self.env.ref('reportes_ministerio_trabajo_py.tipo_entrada_vacaciones')

            if this.struct_id.type_id.structure_type_tag == 'vacacion':
                this.write({'worked_days_line_ids': [(0, 0, {
                    'contract_id': this.contract_id.id,
                    'work_entry_type_id': tipo_entrada_vacaciones.id,
                    'number_of_days': cant_asistencias.get(tipo_entrada_vacaciones.code)['cant_dias'] or 0,
                    'number_of_hours': cant_asistencias.get(tipo_entrada_vacaciones.code)['cant_horas'] or 0,
                })]})
            else:
                for asistencia_key in cant_asistencias.keys():
                    work_entry_types = self.env['hr.work.entry.type'].search([('code', '=', asistencia_key)])
                    for work_entry_type in work_entry_types:
                        this.write({
                            'worked_days_line_ids': [
                                (0, 0, {
                                    'work_entry_type_id': work_entry_type.id,
                                    'number_of_days': cant_asistencias[asistencia_key]['cant_dias'] or 0,
                                    'number_of_hours': cant_asistencias[asistencia_key]['cant_horas'] or 0,
                                }),
                            ]
                        })
        return r

    def action_print_payslip(self):
        # rrhh_payroll/models/hr_payslip.py
        return self.env.ref('rrhh_payroll.recibo').report_action(self)

    def get_dia_laboral(self, date):
        # rrhh_payroll/models/hr_payslip.py
        if not self.es_nomina_vacaciones:
            return 1
        return 0 if self.env['calendario.feriado'].check_feriado(date) else 1


class HRPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    amount = fields.Float()
