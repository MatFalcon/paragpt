# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from odoo import fields, api, models, _
from . import calculo_renuncia as cl
import datetime


def get_mes(mes):
    return {
        1: 'Enero',
        2: 'Febrero',
        3: 'Marzo',
        4: 'Abril',
        5: 'Mayo',
        6: 'Junio',
        7: 'Julio',
        8: 'Agosto',
        9: 'Setiembre',
        10: 'Octubre',
        11: 'Noviembre',
        12: 'Diciembre',
    }.get(mes)


class WizardCalculoRenuncia(models.TransientModel):
    _name = 'wizard.calculo.renuncia'
    _description = 'Wizard para el calculo de renuncia'

    employee_id = fields.Many2one('hr.employee', string='Empleado')
    contract_id = fields.Many2one('hr.contract', string='Contrato')
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True)
    fecha_fin = fields.Date(string='Fecha de Desvinculación', required=True)

    antiguedad = fields.Char(string='Antiguedad', store=True, compute='_get_antiguedad')
    tipo_renuncia = fields.Selection(string="Tipo de Renuncia", selection=[
        ('renuncia', 'Renuncia'),
        ('abandono', 'Abandono de Trabajo'),
        ('fallecimiento', 'Fallecimiento'),
        ('jubilacion', 'Jubilación'),
    ], default='renuncia', required=True)

    periodo_prueba = fields.Boolean(string='Periodo de prueba')
    causa_justificada = fields.Boolean(string='Es causa justificada')

    tipo_empleado = fields.Selection(selection=[('30', 'Mensualero'), ('24', 'Jornalero')], string='Modalidad de pago')
    aporta_ips = fields.Boolean(string='Aporta IPS')
    # aporta_amh = fields.Boolean(string='Aporta AMH')

    # @api.onchange('aporta_ips')
    # def _onchange_aporta_ips(self):
    # if self.aporta_ips:
    # self.aporta_amh = False

    # @api.onchange('aporta_amh')
    # def _onchange_aporta_amh(self):
    #     if self.aporta_amh:
    #         self.aporta_ips = False

    salario_promedio_ultimos_meses = fields.Boolean(string='Conoce el salario promedio de los ultimos 6 meses?')
    salario_mes_1 = fields.Integer(string='Salario mes #1')
    salario_mes_2 = fields.Integer(string='Salario mes #2')
    salario_mes_3 = fields.Integer(string='Salario mes #3')
    salario_mes_4 = fields.Integer(string='Salario mes #4')
    salario_mes_5 = fields.Integer(string='Salario mes #5')
    salario_mes_6 = fields.Integer(string='Salario mes #6')

    salario_promedio = fields.Integer(string='Salario promedio')
    salario_promedio_diario = fields.Integer(string='Salario promedio diario')
    testigo_id = fields.Many2one('hr.employee', string='Testigo')

    dias_mes_aun_no_abonados = fields.Integer(string='Días trabajados en el mes, que aún no fueron abonados')

    dias_preaviso_correspondido = fields.Integer(string='Días correspondidos', compute='_get_preaviso_correspondido', store=True)
    dias_preaviso_recibido = fields.Integer(string='Días recibidos')

    vacaciones_causadas = fields.Integer(string='Días correspondientes', store=True, compute='_get_vacaciones_causadas')
    vacaciones_gozadas = fields.Integer(string='Días gozados')

    vacaciones_proporcionales_correspondientes = fields.Float(string='Días correspondientes', store=True, compute='_get_vacaciones_proporcionales')
    vacaciones_proporcionales_gozadas = fields.Float(string='Días gozados')

    vacaciones_acumuladas = fields.Integer(string='Días Acumulados')

    otros_haberes = fields.Integer(string='Otros Haberes')
    otros_deberes = fields.Integer(string='Otros Deberes')

    liq_salario_dias_trabajados = fields.Integer()
    liq_preaviso = fields.Integer()
    liq_indemnizacion = fields.Integer()
    liq_vacaciones_causadas = fields.Integer()
    liq_vacaciones_proporcionales = fields.Integer()
    liq_vacaciones_acumuladas = fields.Integer()
    liq_subtotal1 = fields.Integer()
    liq_ips = fields.Integer()
    # liq_amh = fields.Integer()
    liq_subtotal2 = fields.Integer()
    liq_aguinaldo_proporcional = fields.Integer()
    liq_total = fields.Integer()

    show_liq_salario_dias_trabajados = fields.Integer(string='Salario por dias trabajados')
    show_liq_preaviso = fields.Integer(string='Preaviso')
    show_liq_indemnizacion = fields.Integer(string='Indemnización')
    show_liq_vacaciones_causadas = fields.Integer(string='Vacaciones causadas')
    show_liq_vacaciones_proporcionales = fields.Integer(string='Vacaciones proporcionales')
    show_liq_vacaciones_acumuladas = fields.Integer(string='Vacaciones acumuladas')
    show_liq_otros_haberes = fields.Integer('Otros Haberes')
    show_liq_otros_deberes = fields.Integer('Otros Deberes')
    show_liq_subtotal1 = fields.Integer(string='Subtotal')
    show_liq_ips = fields.Integer(string='Descuento por IPS(9%)')
    # show_liq_amh = fields.Integer(string='Descuento por AMH(5%)')
    show_liq_subtotal2 = fields.Integer(string='Subtotal')
    show_liq_aguinaldo_proporcional = fields.Integer(string='Aguinaldo proporcional')
    show_liq_total = fields.Integer(string='Total')

    posible_periodo_prueba = fields.Boolean(store=True, compute='_ocultar_campos')
    posible_preaviso = fields.Boolean(store=True, compute='_ocultar_campos')
    base_aguinaldo_proporcional = fields.Selection([
        ('historial_salario', 'Historial de Salarios'),
        ('salario_promedio', 'Salario promedio calculado'),
    ], string='Base para el Aguinaldo Proporcional', default='historial_salario', required=True)

    @api.onchange('tipo_renuncia')
    def onChangeTipoRenuncia(self):
        if self.tipo_renuncia in ['fallecimiento', 'jubilacion']:
            self.dias_preaviso_recibido = self.dias_preaviso_correspondido
            self.vacaciones_gozadas = self.vacaciones_causadas
            self.vacaciones_proporcionales_gozadas = self.vacaciones_proporcionales_correspondientes
            self.vacaciones_acumuladas = 0

    @api.onchange('employee_id', 'contract_id')
    def onChangeEmployeeContract(self):
        def probar_unico_contrato(self):
            contratos_activos = self.employee_id.contract_ids.filtered(lambda contract: contract.state == 'open')
            if len(contratos_activos) == 1:
                self.contract_id = contratos_activos

        def rellenar_salarios(self):
            if self.contract_id:
                self.tipo_empleado = '30'
                self.aporta_ips = True
                if self.tipo_empleado in ['30', '24']:
                    ultimos_salarios = self.env['historial.salario'].search([('state', '=', 'good')], order='date_from desc').filtered(
                        lambda x: x.contract_id == self.contract_id
                    )
                    meses_ultimos_salarios = []
                    for ultimo_salario in ultimos_salarios:
                        if ultimo_salario.date_from.month not in meses_ultimos_salarios:
                            meses_ultimos_salarios.append(ultimo_salario.date_from.month)
                            if len(meses_ultimos_salarios) >= 6:
                                break

                    for i in range(1, 7):
                        if len(meses_ultimos_salarios) >= i:
                            self['salario_mes_' + str(i)] = sum(
                                ultimos_salarios.filtered(lambda x: x.date_from.month == meses_ultimos_salarios[i - 1]).mapped('real_wage')
                            )

                elif self.tipo_empleado == '24':
                    self.salario_promedio_diario = self.contract_id.get_real_wage(self.fecha_fin).get('real_wage')

        if not self.employee_id:
            self.contract_id = False
            self.fecha_inicio = False
        elif not self.contract_id:
            self.fecha_inicio = False
            domain = [('employee_id', '=', self.employee_id.id)]
            probar_unico_contrato(self)
            return {'domain': {'contract_id': domain}}
        else:
            if self.contract_id.employee_id != self.employee_id:
                self.contract_id = False
                domain = [('employee_id', '=', self.employee_id.id)]
                return {'domain': {'contract_id': domain}}
            else:
                self.fecha_inicio = self.contract_id.date_start
                rellenar_salarios(self)
        return

    @api.onchange('salario_mes_1', 'salario_mes_2', 'salario_mes_3', 'salario_mes_4', 'salario_mes_5', 'salario_mes_6')
    def _get_salario_promedio(self):
        if self.tipo_empleado == '30' and not self.salario_promedio_ultimos_meses:
            cl.ipsStatus = self.aporta_ips
            # cl.amhStatus = self.aporta_amh
            salario_ant = []
            if self.salario_mes_1: salario_ant.append(self.salario_mes_1)
            if self.salario_mes_2: salario_ant.append(self.salario_mes_2)
            if self.salario_mes_3: salario_ant.append(self.salario_mes_3)
            if self.salario_mes_4: salario_ant.append(self.salario_mes_4)
            if self.salario_mes_5: salario_ant.append(self.salario_mes_5)
            if self.salario_mes_6: salario_ant.append(self.salario_mes_6)

            cl.calcular_salarios(self.tipo_empleado, self.salario_promedio_ultimos_meses, salario_ant)
            self.salario_promedio = cl.salario_promedio

    @api.onchange('salario_promedio_ultimos_meses')
    def onChangeKnowSalarioPromedio(self):
        self.salario_promedio = 0
        self.salario_mes_1 = 0
        self.salario_mes_2 = 0
        self.salario_mes_3 = 0
        self.salario_mes_4 = 0
        self.salario_mes_5 = 0
        self.salario_mes_6 = 0

    @api.onchange('salario_promedio')
    def _get_salario_promedio_diario(self):
        if self.salario_promedio:
            if self.salario_promedio_ultimos_meses:
                cl.salario_promedio = self.salario_promedio
                cl.calcular_salarios(self.tipo_empleado, self.salario_promedio_ultimos_meses)
                self.salario_promedio_diario = cl.salario_diario
            else:
                cl.salario_promedio = self.salario_promedio
                self.salario_promedio_diario = cl.salario_diario
        else:
            self.salario_promedio_diario = 0

    @api.onchange('fecha_inicio', 'fecha_fin', 'causa_justificada')
    def _get_antiguedad(self):
        if self.fecha_inicio and self.fecha_fin:
            cl.calcular_antiguedad(self.fecha_inicio, self.fecha_fin, self.causa_justificada)
            diferencia = get_diferencia_tiempo(self.fecha_inicio, self.fecha_fin)
            antiguedad = ''
            antiguedad += str(diferencia['years']) + ' ' + ('años' if diferencia['years'] != 1 else 'año') + ', '
            antiguedad += str(diferencia['months']) + ' ' + ('meses' if diferencia['months'] != 1 else 'mes') + ', '
            antiguedad += str(diferencia['days']) + ' ' + ('dias' if diferencia['days'] != 1 else 'dia') + ', '
            self.antiguedad = antiguedad

    @api.onchange('fecha_inicio', 'fecha_fin')
    def _get_dias_trabajados_no_pagados(self):
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin:
                self.dias_mes_aun_no_abonados = (self.fecha_fin.day - ((self.fecha_inicio.day - 1)
                                                                       if self.fecha_inicio.month == self.fecha_fin.month
                                                                       else 0
                                                                       ) if self.fecha_fin.day <= 30 else 30)

    @api.onchange('fecha_inicio', 'fecha_fin')
    def _get_preaviso_correspondido(self):
        if self.fecha_inicio and self.fecha_fin:
            diferencia = get_diferencia_tiempo(self.fecha_inicio, self.fecha_fin)
            self.dias_preaviso_correspondido = cl.getPreaviso(diferencia['years'])
            a = 0

    @api.onchange('fecha_inicio', 'fecha_fin')
    def _get_vacaciones_causadas(self):
        if self.fecha_inicio and self.fecha_fin:
            diferencia = get_diferencia_tiempo(self.fecha_inicio, self.fecha_fin)
            self.vacaciones_causadas = cl.getVacaciones(diferencia['years'])

    @api.onchange('fecha_inicio', 'fecha_fin')
    def _get_vacaciones_proporcionales(self):
        if self.fecha_inicio and self.fecha_fin:
            self.vacaciones_proporcionales_correspondientes = cl.getVacacionesProp()

    @api.onchange('fecha_inicio', 'fecha_fin')
    def _ocultar_campos(self):
        posible_periodo_prueba = False
        posible_preaviso = False
        if self.fecha_inicio and self.fecha_fin:
            diferencia = get_diferencia_tiempo(self.fecha_inicio, self.fecha_fin)
            if not diferencia['years']:
                if (diferencia['months']) < 3 or (diferencia['months'] == 3 and not diferencia['days']):
                    posible_periodo_prueba = True
                else:
                    posible_preaviso = True
            else:
                posible_preaviso = True

        self.posible_preaviso = posible_preaviso
        self.posible_periodo_prueba = posible_periodo_prueba

    def get_total_brutos_en_este_ano(self, salarios_este_ano):
        total_brutos_en_este_ano = sum((salario_este_ano.bruto_para_aguinaldo or 0) for salario_este_ano in salarios_este_ano)
        if total_brutos_en_este_ano:
            total_brutos_en_este_ano /= 12
        else:
            total_brutos_en_este_ano = 0
        return total_brutos_en_este_ano

    @api.onchange('causa_justificada', 'periodo_prueba', 'antiguedad', 'aporta_ips', 'salario_promedio_diario', 'dias_mes_aun_no_abonados',
                  'dias_preaviso_recibido', 'vacaciones_gozadas', 'vacaciones_proporcionales_gozadas', 'vacaciones_acumuladas', 'otros_haberes',
                  'otros_deberes', 'base_aguinaldo_proporcional')
    def _get_liquidacion_final(self):
        if self.fecha_inicio and self.fecha_fin and self.salario_promedio_diario:
            fecha_inicio = self.fecha_inicio
            fecha_fin = self.fecha_fin
            antiguedadOj = get_diferencia_tiempo(fecha_inicio, fecha_fin)
            cl.ipsStatus = self.aporta_ips
            # cl.amhStatus = self.aporta_amh
            cl.getLiquidacion(
                Sueldo_Prom_Diario=self.salario_promedio_diario,
                preaviso_Correspondido=self.dias_preaviso_correspondido,
                preaviso_Dado=self.dias_preaviso_recibido,
                vacaciones_Causada=self.vacaciones_causadas,
                vacaciones_Causada_Dadas=self.vacaciones_gozadas,
                vacaciones_Correspondida=self.vacaciones_proporcionales_correspondientes,
                vacaciones_Dada=self.vacaciones_proporcionales_gozadas,
                vacaciones_Atrasadas=self.vacaciones_acumuladas,
                fecha_inicio_a=fecha_inicio.year,
                fecha_inicio_m=fecha_inicio.month,
                fecha_inicio_d=fecha_inicio.day,
                fecha_final_a=fecha_fin.year,
                fecha_final_m=fecha_fin.month,
                fecha_final_d=fecha_fin.day,
                antiguedadOj=antiguedadOj,
                perprueba=self.periodo_prueba,
                justificada=self.causa_justificada,
                otros_haberes=self.otros_haberes,
                otros_deberes=self.otros_deberes,
                posible_preaviso=self.posible_preaviso,
                salario_diario_real=self.contract_id.get_computed_daily_wage(self.fecha_fin),
                dias_mes_aun_no_abonados=self.dias_mes_aun_no_abonados,
            )

            self.liq_salario_dias_trabajados = cl.liq_diasTrabaj
            self.liq_preaviso = cl.liq_Preaviso if self.posible_preaviso else 0
            self.liq_indemnizacion = cl.liq_indemnizacion
            self.liq_vacaciones_causadas = cl.liq_vaCau
            self.liq_vacaciones_proporcionales = cl.liq_vaPropor
            self.liq_vacaciones_acumuladas = cl.liq_vaCauAnt
            self.liq_subtotal1 = cl.liq_SubTot_1
            self.liq_ips = cl.liq_ips
            # self.liq_amh = cl.liq_amh
            self.liq_subtotal2 = cl.liq_SubTot_2
            self.liq_aguinaldo_proporcional = cl.liq_aquin
            self.liq_total = cl.liq_SubTot_3

            self.show_liq_salario_dias_trabajados = cl.liq_diasTrabaj
            self.show_liq_preaviso = -1 * (cl.liq_Preaviso if self.posible_preaviso else 0)
            self.show_liq_indemnizacion = cl.liq_indemnizacion
            self.show_liq_vacaciones_causadas = cl.liq_vaCau
            self.show_liq_vacaciones_proporcionales = cl.liq_vaPropor
            self.show_liq_vacaciones_acumuladas = cl.liq_vaCauAnt
            self.show_liq_otros_haberes = self.otros_haberes
            self.show_liq_otros_deberes = -1 * (self.otros_deberes)
            self.show_liq_subtotal1 = cl.liq_SubTot_1
            self.show_liq_ips = cl.liq_ips
            # self.show_liq_amh = cl.liq_amh
            self.show_liq_subtotal2 = cl.liq_SubTot_2
            self.show_liq_aguinaldo_proporcional = cl.liq_aquin
            self.show_liq_total = cl.liq_SubTot_3

            if self.base_aguinaldo_proporcional == 'historial_salario':
                salarios_este_ano = self.env['historial.salario'].search([('state', '=', 'good')],
                                                                         order='date_from desc').filtered(
                    lambda x: x.contract_id == self.contract_id and x.date_from.year == self.fecha_fin.year
                )

                total_brutos_en_este_ano = self.get_total_brutos_en_este_ano(salarios_este_ano)
                if total_brutos_en_este_ano:
                    total_brutos_en_este_ano += (self.liq_vacaciones_proporcionales + self.liq_salario_dias_trabajados) / 12
                    liq_aguinaldo_proporcional_anterior = self.liq_aguinaldo_proporcional
                    self.liq_aguinaldo_proporcional = total_brutos_en_este_ano
                    self.show_liq_aguinaldo_proporcional = total_brutos_en_este_ano

                    self.liq_total = self.liq_total - liq_aguinaldo_proporcional_anterior + total_brutos_en_este_ano

            if self.liq_subtotal2 < 0:
                self.liq_ips = 0
                self.show_liq_ips = 0
            self.show_liq_total = self.liq_total

            if self.causa_justificada:
                self.liq_preaviso = 0
                self.show_liq_preaviso = self.liq_preaviso

    def let_the_purge_begin(self):
        self._get_antiguedad()
        self._get_preaviso_correspondido()
        self._get_vacaciones_causadas()
        self._get_vacaciones_proporcionales()

        name = ''
        motivo = ''
        if self.tipo_renuncia in ['renuncia']:
            name = 'Renuncia'
            motivo = 'Renuncia'
        elif self.tipo_renuncia in ['fallecimiento']:
            name = 'Renuncia por fallecimiento'
            motivo = 'Renuncia - Fallecimiento'
        elif self.tipo_renuncia in ['abandono']:
            name = 'Renuncia por abandono de trabajo'
            motivo = 'Renuncia - Abandono de Trabajo'
        elif self.tipo_renuncia in ['jubilacion']:
            name = 'Jubilación'
            motivo = 'Renuncia - Jubilación'

        name_lote = 'Liquidaciones de Salarios - Renuncias ' + \
                    get_mes(self.fecha_fin.month) + ' ' + \
                    str(self.fecha_fin.year)
        payslip_run_id = self.env['hr.payslip.run'].search([
            ('name', '=', name_lote),
            ('company_id', '=', self.contract_id.company_id.id),
        ])
        if not payslip_run_id:
            payslip_run_id = payslip_run_id.create({
                'company_id': self.contract_id.company_id.id,
                'name': name_lote,
                'date_start': self.fecha_fin.replace(day=1),
                'date_end': self.fecha_fin.replace(day=fields.Date().end_of(self.fecha_fin, 'month').day),
            })

        payslip = self.env['hr.payslip'].create({
            'name': name + ' - ' + self.contract_id.name,
            'employee_id': self.employee_id.id,
            'testigo_id': self.testigo_id.id,
            'contract_id': self.contract_id.id,
            'date_from': self.fecha_fin,
            'date_to': self.fecha_fin,
            'payslip_run_id': payslip_run_id.id,
            'struct_id': self.contract_id.company_id.payroll_structure_default_renuncia.id,
            'es_liquidacion': True,
            'liquidacion_dias_tabajados': self.dias_mes_aun_no_abonados,
            'liquidacion_antiguedad': self.antiguedad,
            'liquidacion_fecha_inicio': self.fecha_inicio,
            'liquidacion_fecha_fin': self.fecha_fin,
            'liquidacion_motivo': motivo,
            'liquidacion_preaviso_sin_comunicar': (
                    self.dias_preaviso_correspondido - self.dias_preaviso_recibido
            ) if self.posible_preaviso else 0,
            'liquidacion_dias_vacaciones_causadas': self.vacaciones_causadas - self.vacaciones_gozadas,
            'liquidacion_dias_vacaciones_proporcionales': self.vacaciones_proporcionales_correspondientes - self.vacaciones_proporcionales_gozadas,
            'liquidacion_dias_vacaciones_acumuladas': self.vacaciones_acumuladas,
            'input_line_ids': [
                (0, 0, {
                    'input_type_id': self.env.ref(
                        'rrhh_liquidacion.payslip_input_liquidacion_salario_dias_trabajados').id,
                    'amount': self.liq_salario_dias_trabajados,
                }),
                (0, 0, {
                    'input_type_id': self.env.ref(
                        'rrhh_liquidacion.payslip_input_liquidacion_preaviso').id,
                    'amount': self.liq_preaviso,
                }),
                # (0, 0, {
                #     'input_type_id': self.env.ref(
                #         'rrhh_liquidacion.payslip_input_liquidacion_indemnizacion').id,
                #     'amount': self.liq_indemnizacion,
                # }),
                (0, 0, {
                    'input_type_id': self.env.ref(
                        'rrhh_liquidacion.payslip_input_liquidacion_vac_causadas').id,
                    'amount': self.liq_vacaciones_causadas,
                }),
                (0, 0, {
                    'input_type_id': self.env.ref(
                        'rrhh_liquidacion.payslip_input_liquidacion_vac_proporcionales').id,
                    'amount': self.liq_vacaciones_proporcionales,
                }),
                (0, 0, {
                    'input_type_id': self.env.ref(
                        'rrhh_liquidacion.payslip_input_liquidacion_vac_acumuladas').id,
                    'amount': self.liq_vacaciones_acumuladas,
                }),
                (0, 0, {
                    'input_type_id': self.env.ref(
                        'rrhh_liquidacion.payslip_input_liquidacion_aguinaldo').id,
                    'amount': self.liq_aguinaldo_proporcional,
                }),
                (0, 0, {
                    'input_type_id': self.env.ref(
                        'rrhh_liquidacion.payslip_input_otros_haberes').id,
                    'amount': self.otros_haberes,
                }),
                (0, 0, {
                    'input_type_id': self.env.ref(
                        'rrhh_liquidacion.payslip_input_otros_deberes').id,
                    'amount': self.otros_deberes,
                }),
                # (0, 0, {
                #     'input_type_id': self.env.ref(
                #         'rrhh_liquidacion.payslip_input_liquidacion_ips').id,
                #     'amount': self.liq_ips,
                # }),
                # (0, 0, {
                #     'input_type_id': self.env.ref(
                #         'rrhh_liquidacion.payslip_input_liquidacion_amh').id,
                #     'amount': self.liq_amh,
                # }),
            ]
        })
        return {
            'name': _("Prueba"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'hr.payslip',
            'res_id': payslip.id,
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'domain': '[]',
            # 'context': context
        }


def get_diferencia_tiempo(inicio, fin):
    if inicio > fin:
        aux = inicio
        inicio = fin
        fin = aux

    diferencia = {
        'years': relativedelta(fin, inicio).years,
        'months': relativedelta(fin, inicio).months,
        'days': relativedelta(fin, inicio).days
    }

    return diferencia
