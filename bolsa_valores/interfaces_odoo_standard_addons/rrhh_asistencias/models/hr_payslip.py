# -*- coding: utf-8 -*-
import pytz, datetime
from odoo import models, fields, api, exceptions, _
from odoo.addons.reportes_ministerio_trabajo_py.models import amount_to_text_spanish
from dateutil.relativedelta import relativedelta


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def get_mes(self, mes):
        # rrhh_asistencias/models/hr_payslip.py
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

    def to_word(self, numero):
        # rrhh_asistencias/models/hr_payslip.py
        return amount_to_text_spanish.to_word(numero)

    def get_asistencias_totales(self):
        # rrhh_asistencias/models/hr_payslip.py
        cant_asistencias = super(HrPayslip, self).get_asistencias_totales()
        asistencias = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id)])
        date_aux = self.date_from
        ausencias_dias = []
        fix_number_of_work_days = False
        if self.wage_type not in ['monthly']:
            if self.wage_type != 'daily' or not self.contract_id.number_of_planned_work_days:
                cant_asistencias['WORK100']['cant_dias'] = 0
                cant_asistencias['WORK100']['cant_horas'] = 0

                cant_asistencias['AUS']['cant_dias'] = 0
                cant_asistencias['AUS']['cant_horas'] = 0
            else:
                fix_number_of_work_days = True

        while date_aux <= self.date_to:

            asistencias_entrada = asistencias.filtered(
                lambda a: a.entrada_marcada and a.date == date_aux
            )

            cant_asistencias['LLA']['cant_dias'] += sum(
                [1 for asistencia_entrada in asistencias_entrada if
                 asistencia_entrada.llegada_anticipada and asistencia_entrada.se_procesa_llegada_anticipada]
            )
            cant_asistencias['LLA']['cant_horas'] += sum(
                asistencias_entrada.filtered(lambda a: a.se_procesa_llegada_anticipada).mapped(
                    'llegada_anticipada')
            )

            cant_asistencias['LLT']['cant_dias'] += sum(
                [1 for asistencia_entrada in asistencias_entrada if
                 asistencia_entrada.llegada_tardia and asistencia_entrada.se_procesa_llegada_tardia]
            )
            cant_asistencias['LLT']['cant_horas'] += sum(
                asistencias_entrada.filtered(lambda a: a.se_procesa_llegada_tardia).mapped('llegada_tardia')
            )

            asistencias_salida = asistencias.filtered(
                lambda a: a.salida_marcada and a.date == date_aux
            )

            cant_asistencias['HEX50']['cant_dias'] += sum(
                [1 for asistencia_salida in asistencias_salida if
                 asistencia_salida.horas_extra_50 and asistencia_salida.se_procesa_horas_extra_50]
            )
            cant_asistencias['HEX50']['cant_horas'] += sum(
                asistencias_salida.filtered(lambda a: a.se_procesa_horas_extra_50).mapped('horas_extra_50')
            )

            cant_asistencias['HEX100']['cant_dias'] += sum(
                [1 for asistencia_salida in asistencias_salida if
                 asistencia_salida.horas_extra_100 and asistencia_salida.se_procesa_horas_extra_100]
            )
            cant_asistencias['HEX100']['cant_horas'] += sum(
                asistencias_salida.filtered(lambda a: a.se_procesa_horas_extra_100).mapped('horas_extra_100')
            )

            cant_asistencias['HEXNOC']['cant_dias'] += sum(
                [1 for asistencia_salida in asistencias_salida if
                 asistencia_salida.horas_extra_nocturnas and asistencia_salida.se_procesa_horas_extra_nocturnas]
            )
            cant_asistencias['HEXNOC']['cant_horas'] += sum(
                asistencias_salida.filtered(lambda a: a.se_procesa_horas_extra_nocturnas).mapped('horas_extra_nocturnas')
            )

            cant_asistencias['HNOC']['cant_dias'] += sum(
                [1 for asistencia_salida in asistencias_salida if
                 asistencia_salida.horas_nocturnas and asistencia_salida.se_procesa_horas_nocturnas]
            )
            cant_asistencias['HNOC']['cant_horas'] += sum(
                asistencias_salida.filtered(lambda a: a.se_procesa_horas_nocturnas).mapped('horas_nocturnas')
            )

            cant_asistencias['SAA']['cant_dias'] += sum(
                [1 for asistencia_salida in asistencias_salida if
                 asistencia_salida.salida_anticipada and asistencia_salida.se_procesa_salida_anticipada]
            )
            cant_asistencias['SAA']['cant_horas'] += sum(
                asistencias_salida.filtered(lambda a: a.se_procesa_salida_anticipada).mapped('salida_anticipada')
            )

            cant_asistencias['HTP']['cant_dias'] += sum(
                [1 for asistencia_salida in asistencias_salida if
                 asistencia_salida.total_plus_horario and asistencia_salida.se_procesa_plus_hora]
            )
            cant_asistencias['HTP']['cant_horas'] += sum(
                asistencias_salida.filtered(lambda a: a.se_procesa_plus_hora).mapped('total_plus_horario')
            )

            cant_asistencias['HMX']['cant_dias'] += sum(
                [1 for asistencia_salida in asistencias_salida if
                 asistencia_salida.total_mix_horario and asistencia_salida.se_procesa_mix_hora]
            )
            cant_asistencias['HMX']['cant_horas'] += sum(
                asistencias_salida.filtered(lambda a: a.se_procesa_mix_hora).mapped('total_mix_horario')
            )

            if not (asistencias_entrada or asistencias_salida) and date_aux not in ausencias_dias:
                if not self.env['calendario.feriado'].check_feriado(date_aux) and (
                        self.contract_id.get_entrada_planeada(date_aux) or
                        self.contract_id.get_salida_planeada(date_aux)
                ) and not self.env['hr.leave'].search([('state', '=', 'validate'),
                                                       ('contract_id', '=', self.contract_id.id),
                                                       ('request_date_from', '<=', date_aux),
                                                       ('request_date_to', '>=', date_aux),
                                                       ]):
                    ausencias_dias.append(date_aux)
            elif self.wage_type not in ['monthly'] and (asistencias_entrada or asistencias_salida) and not fix_number_of_work_days:
                cant_asistencias['WORK100']['cant_dias'] += 1
                cant_asistencias['WORK100']['cant_horas'] += 8

            date_aux += datetime.timedelta(days=1)

        if self.wage_type in ['monthly'] and self.employee_id.no_attendance_is_absence: cant_asistencias['AUS']['cant_dias'] = len(ausencias_dias)

        # Paso necesario para evitar problemas con exceso de decimales
        for cant_asistencia in cant_asistencias:
            cant_asistencias[cant_asistencia]['cant_dias'] = round(cant_asistencias[cant_asistencia]['cant_dias'], 2)
            cant_asistencias[cant_asistencia]['cant_horas'] = round(cant_asistencias[cant_asistencia]['cant_horas'], 2)

        return cant_asistencias

    def action_payslip_done(self):
        # rrhh_asistencias/models/hr_payslip.py
        self.compute_sheet()
        return super(HrPayslip, self).action_payslip_done()

    def action_payslip_cancel(self):
        # rrhh_asistencias/models/hr_payslip.py
        self.filtered(lambda x: x.state == 'done').action_payslip_draft()
        return super(HrPayslip, self).action_payslip_cancel()
