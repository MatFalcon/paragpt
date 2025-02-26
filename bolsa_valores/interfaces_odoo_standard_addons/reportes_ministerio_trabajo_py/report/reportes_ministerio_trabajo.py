# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, addons, http
from odoo.http import request
import base64, datetime, calendar, os, xlsxwriter, re, shutil


def get_monthrange(year, month):
    return (calendar.monthrange(int(year), int(month)))[1]


class EmpleadosYObrerosZIP(models.Model):
    _name = 'empleados_y_obreros_zip_model'
    _description = 'Modelo auxiliar para la generación de reportes'

    wizard_id = fields.Many2one('reportes_ministerio_trabajo', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Compañía')
    month = fields.Selection(selection=[
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3', 'Marzo'),
        ('4', 'Abril'),
        ('5', 'Mayo'),
        ('6', 'Junio'),
        ('7', 'Julio'),
        ('8', 'Agosto'),
        ('9', 'Setiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
    ], required=True, string='Mes')
    year = fields.Integer(string='Año')
    report_date_start = fields.Date(compute='_get_report_date')
    report_date_end = fields.Date(compute='_get_report_date')

    is_report_for_xlsx = fields.Boolean(default=False)

    def _get_report_date(self):
        for this in self:
            this.report_date_end = tools.datetime.strptime(
                str(this.year) + '-' + this.month + '-' + str(get_monthrange(this.year, int(this.month))),
                '%Y-%m-%d'
            ).date()
            this.report_date_start = this.report_date_end.replace(day=1)

    def get_motivo_salida(self, contract):
        return ''

    def comprobar_dia(self, dia, month, contract, force_check_active_contract=False):
        dia_datetime = datetime.datetime.strptime(str(self.year) + '-' + str(month) + '-' + str(dia),
                                                  '%Y-%m-%d').date()
        if force_check_active_contract:
            if dia_datetime < contract.date_start or (contract.date_end and dia_datetime > contract.date_end):
                return 0
        if dia_datetime.weekday() == 6:
            return 'D'
        elif self.env['calendario.feriado'].check_feriado(dia_datetime):
            return 'F'
        elif self.env['notificacion.vacacion'].search([
            ('contract_id', '=', contract.id),
            ('state', '=', 'done'),
            ('fecha_inicio_vacaciones', '<=', dia_datetime),
            ('fecha_fin_vacaciones', '>=', dia_datetime)
        ]):
            return 'V'
        elif self.env['hr.leave'].search([
            ('holiday_status_id.appears_in_mtess_reports', '=', True),
            ('contract_id', '=', contract.id),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', dia_datetime),
            ('request_date_to', '>=', dia_datetime),
            ('holiday_status_id.code', 'in', ['REP', 'REPO'])
        ]):
            return 'REP'
        elif dia_datetime < contract.date_start:
            return 'E'
        elif (contract.date_end and dia_datetime > contract.date_end):
            return 'S'
        elif dia_datetime.weekday() == 5 and contract.company_id.sueldos_y_jornales_report_dias_sabado_valor and contract.company_id.sueldos_y_jornales_report_dias_sabado_valor != 'normal':
            return int(contract.company_id.sueldos_y_jornales_report_dias_sabado_valor)
        else:
            return 8

    def get_payslips_normal(self, payslips):
        return payslips.filtered(lambda payslip: payslip.struct_id.type_id.structure_type_tag == 'normal')

    def get_payslips_aguinaldo(self, payslips):
        return payslips.filtered(lambda payslip: payslip.struct_id.type_id.structure_type_tag == 'aguinaldo')

    def get_payslips_liquidacion(self, payslips):
        return payslips.filtered(lambda payslip: payslip.struct_id.type_id.structure_type_tag == 'liquidacion')

    def get_payslips_vacacion(self, payslips):
        return payslips.filtered(lambda payslip: payslip.struct_id.type_id.structure_type_tag == 'vacacion')

    def create_empleados_obreros_xlsx_file(self, dt):
        # os.chdir('/tmp')
        foldername = "Reportes EyO SyJ " + dt
        folderpath = foldername
        company_foldername = folderpath + "/" + self.company_id.name.replace("'", "")
        workbook = xlsxwriter.Workbook(
            company_foldername +
            '/Empleados y Obreros ' +
            str(self.year) +
            ' - ' +
            self.company_id.name.replace("'", "") +
            ' - ' +
            (self.company_id.nro_patronal or '') +
            '.xlsx'
        )
        global sheet
        global bold
        global number
        global date_only
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Datos'[:31])
        bold = workbook.add_format({'bold': True})
        number = workbook.add_format({'num_format': '0'})
        date_only = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        position_x = 0
        position_y = 0

        def addSalto():
            global position_x
            global position_y
            position_x = 0
            position_y += 1

        def addRight():
            global position_x
            position_x += 1

        def simpleWrite(to_write, format=None):
            global sheet
            if isinstance(to_write, int) or isinstance(to_write, float):
                to_write = int(to_write)
            sheet.write(position_y, position_x, to_write or ('' if type(to_write) != int else 0), format)

        def breakAndWrite(to_write, format=None):
            global sheet
            addSalto()
            simpleWrite(to_write, format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            simpleWrite(to_write, format)

        simpleWrite('NROPATRONAL')
        rightAndWrite('DOCUMENTO')
        rightAndWrite('NOMBRE')
        rightAndWrite('APELLIDO')
        rightAndWrite('SEXO')
        rightAndWrite('ESTADOCIVIL')
        rightAndWrite('FECHANAC')
        rightAndWrite('NACIONALIDAD')
        rightAndWrite('DOMICILIO')
        rightAndWrite('FECHANACMENOR')
        rightAndWrite('HIJOSMENORES')
        rightAndWrite('CARGO')
        rightAndWrite('PROFESION')
        rightAndWrite('FECHAENTRADA')
        rightAndWrite('HORARIOTRABAJO')
        rightAndWrite('MENORESCAPA')
        rightAndWrite('MENORESESCOLAR')
        rightAndWrite('FECHASALIDA')
        rightAndWrite('MOTIVOSALIDA')
        rightAndWrite('ESTADO')
        contracts = self.env['hr.contract.active_history'].search([
            ('contract_id', '!=', False),
            ('contract_id.employee_id', '!=', False),
            ('contract_id.company_id', '=', self.company_id.id),
        ]).filtered(lambda contract_active_history:
                    contract_active_history.date_start.year <= self.year and
                    (
                            not contract_active_history.date_end or
                            contract_active_history.date_end.year >= self.year
                    )
                    ).mapped('contract_id').sorted(
            key=lambda contract: ((contract.employee_id.apellido or ''), (contract.employee_id.nombre or ''))
        )
        if not contracts:
            breakAndWrite(self.company_id.nro_patronal)
            rightAndWrite(0, number)
            rightAndWrite('Sin Registro')
            rightAndWrite('de Personal')
            rightAndWrite('n')
            rightAndWrite('n')
            rightAndWrite(0, date_only)
            rightAndWrite('-')
            rightAndWrite('-')
            addRight()

            rightAndWrite(0, number)
            rightAndWrite('-')
            rightAndWrite('-')
            rightAndWrite(0, date_only)
            addRight()
            addRight()
            addRight()
            addRight()
            addRight()
            rightAndWrite('I')
        for contract in contracts:
            breakAndWrite(self.company_id.nro_patronal)
            rightAndWrite(contract.employee_id.identification_id)
            rightAndWrite(contract.employee_id.nombre)
            rightAndWrite(contract.employee_id.apellido)
            rightAndWrite({
                              'male': 'M',
                              'female': 'F'
                          }.get(contract.employee_id.gender))
            rightAndWrite({
                              'single': 'S',
                              'married': 'C',
                              'cohabitant': '',
                              'widower': 'V',
                              'divorced': 'D',
                              'menor': '',
                          }.get(contract.employee_id.marital) if contract.employee_id.marital else '')
            rightAndWrite(contract.employee_id.birthday if contract.employee_id.birthday else '', date_only)
            rightAndWrite(
                {
                    'Bolivia': 'Boliviano',
                    'Paraguay': 'Paraguaya',
                    'Alemania': 'Aleman',
                    'Brasil': 'Brasilero',
                    'Canadá': 'Canadiense'
                }.get(contract.employee_id.country_id.name) if contract.employee_id.country_id else 'Paraguaya'
            )
            direccion = []
            if contract.employee_id.address_home_id.state_id:
                direccion.append(contract.employee_id.address_home_id.state_id.name)
            if contract.employee_id.address_home_id.city:
                direccion.append(contract.employee_id.address_home_id.city)
            if contract.employee_id.address_home_id.street:
                direccion.append(contract.employee_id.address_home_id.street)
            if direccion:
                rightAndWrite(' + '.join(direccion))
            else:
                addRight()
            underage_children_ids = contract.employee_id.children_ids.filtered(lambda children:
                                                                               children._get_age(explicit_date=self.report_date_end, return_age=True) < 18
                                                                               )
            rightAndWrite(min(underage_children_ids.mapped('birthday')) if underage_children_ids else '', date_only)
            rightAndWrite(contract.employee_id.underage_children_count)
            rightAndWrite(contract.job_id.name or '')
            rightAndWrite(contract.employee_id.job_id.name or '')
            rightAndWrite(contract.date_start, date_only)
            addRight()
            addRight()
            addRight()
            fecha_salida = contract.date_end if contract.date_end and contract.date_end.year == self.year else False
            if fecha_salida:
                rightAndWrite(fecha_salida, date_only)
                rightAndWrite(contract.employee_id.departure_reason_id.name or '', date_only)
                # departure_array = []
                # departure_description = ''
                # if contract.employee_id.departure_reason_id.name: departure_array.append(contract.employee_id.departure_reason_id.name)
                # if contract.employee_id.departure_description: departure_array.append(contract.employee_id.departure_description)
                # if departure_array:
                #     departure_description = (' - '.join(departure_array))
                #     regex = re.compile(r'<[^>]+>')
                #     departure_description = regex.sub('', departure_description)
                # if not departure_description:
                #     departure_description = 'Finalización de Contrato'
                # rightAndWrite(departure_description)
                rightAndWrite('Inactivo')
            else:
                addRight()
                addRight()
                rightAndWrite('Activo')
        workbook.close()

    def create_sueldos_y_jornales_xlsx_file(self, dt):
        # os.chdir('/tmp')
        foldername = "Reportes EyO SyJ " + dt
        folderpath = foldername
        company_foldername = folderpath + "/" + self.company_id.name.replace("'", "")
        workbook = xlsxwriter.Workbook(
            company_foldername +
            '/Sueldos y Jornales ' +
            str(self.year) +
            ' - ' +
            self.company_id.name.replace("'", "") +
            ' - ' +
            (self.company_id.nro_patronal or '') +
            '.xlsx'
        )
        global sheet
        global bold
        global number
        global date_only
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Datos'[:31])
        bold = workbook.add_format({'bold': True})
        number = workbook.add_format({'num_format': '0'})
        date_only = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        position_x = 0
        position_y = 0

        def addSalto():
            global position_x
            global position_y
            position_x = 0
            position_y += 1

        def addRight():
            global position_x
            position_x += 1

        def simpleWrite(to_write, format=None):
            global sheet
            if isinstance(to_write, int) or isinstance(to_write, float):
                to_write = int(to_write)
            sheet.write(position_y, position_x, to_write or ('' if type(to_write) != int else 0), format)

        def breakAndWrite(to_write, format=None):
            global sheet
            addSalto()
            simpleWrite(to_write, format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            simpleWrite(to_write, format)

        simpleWrite('NROPATRONAL')
        rightAndWrite('DOCUMENTO')
        rightAndWrite('FORMADEPAGO')
        rightAndWrite('IMPORTEUNITARIO')
        rightAndWrite('H_ENE')
        rightAndWrite('S_ENE')
        rightAndWrite('H_FEB')
        rightAndWrite('S_FEB')
        rightAndWrite('H_MAR')
        rightAndWrite('S_MAR')
        rightAndWrite('H_ABR')
        rightAndWrite('S_ABR')
        rightAndWrite('H_MAY')
        rightAndWrite('S_MAY')
        rightAndWrite('H_JUN')
        rightAndWrite('S_JUN')
        rightAndWrite('H_JUL')
        rightAndWrite('S_JUL')
        rightAndWrite('H_AGO')
        rightAndWrite('S_AGO')
        rightAndWrite('H_SET')
        rightAndWrite('S_SET')
        rightAndWrite('H_OCT')
        rightAndWrite('S_OCT')
        rightAndWrite('H_NOV')
        rightAndWrite('S_NOV')
        rightAndWrite('H_DIC')
        rightAndWrite('S_DIC')
        rightAndWrite('H_50')
        rightAndWrite('S_50')
        rightAndWrite('H_100')
        rightAndWrite('S_100')
        rightAndWrite('AGUINALDO')
        rightAndWrite('BENEFICIOS')
        rightAndWrite('BONIFICACIONES')
        rightAndWrite('VACACIONES')
        rightAndWrite('TOTAL_H')
        rightAndWrite('TOTAL_S')
        rightAndWrite('TOTALGENERAL')

        payslips_all = self.env['hr.payslip'].search([
            ('state', 'in', ['done', 'paid']),
            ('contract_id.company_id', '=', self.company_id.id),
        ]).filtered(lambda slip: slip.date_to.year == self.year)
        contracts = payslips_all.mapped('contract_id')
        if not contracts:
            breakAndWrite(0, number)
            for i in range(0, 38):
                rightAndWrite(0, number)
        for contract in contracts:
            payslips = payslips_all.search([('id', 'in', payslips_all.ids), ('contract_id', '=', contract.id)])
            total_horas = 0
            total_salario = 0
            total_aguinaldo = 0
            total_bonificacion_familiar = 0
            total_horas_extras_50_cant = 0
            total_horas_extras_100_cant = 0
            total_horas_extras_50_monto = 0
            total_horas_extras_100_monto = 0
            total_liquidacion_beneficios_monto = 0

            breakAndWrite(self.company_id.nro_patronal)
            rightAndWrite(contract.employee_id.identification_id)
            rightAndWrite({
                              False: 'M',
                              'monthly': 'M',
                              'daily': 'J',
                              'hourly': 'H',
                          }.get(contract.wage_type))
            rightAndWrite(contract.get_computed_daily_wage(tools.datetime.strptime('3112' + str(self.year), '%d%m%Y').date()), number)

            for month in range(1, 13):
                salario_mes = 0
                cantidad_horas_mes = 0
                for dia in range(1, (get_monthrange(self.year, month) + 1)):
                    comprobar_dia_result = self.comprobar_dia(dia, month, contract, force_check_active_contract=True)
                    cantidad_horas_mes += (
                        comprobar_dia_result if isinstance(comprobar_dia_result, int) else 0
                    )
                total_horas += cantidad_horas_mes

                payslips_mes_normal = payslips.filtered(lambda payslip: payslip.date_from.month == month)
                payslips_mes_normal = self.get_payslips_normal(payslips_mes_normal)
                payslips_mes_liquidacion = payslips.filtered(lambda payslip: payslip.date_to.month == month)
                payslips_mes_liquidacion = self.get_payslips_liquidacion(payslips_mes_liquidacion)

                salario_mes += sum(payslips_mes_normal.mapped('line_ids').filtered(
                    lambda line: line.code in ['GROSS', 'ADE']
                ).mapped('total'))
                salario_mes += sum(payslips_mes_liquidacion.mapped('line_ids').filtered(
                    lambda line: line.code in ['DTRAB']
                ).mapped('total'))

                salario_bonificacion_familiar = sum((payslips_mes_normal + payslips_mes_liquidacion).mapped('line_ids').filtered(
                    lambda line: line.code in self.company_id.sueldos_y_jornales_report_codigos_bonificacion_familiar
                ).mapped('total'))
                salario_horas_extra_mes_50 = sum(payslips_mes_normal.mapped('line_ids').filtered(
                    lambda line: line.code in self.company_id.sueldos_y_jornales_report_codigos_hex_50
                ).mapped('total'))
                salario_horas_extra_mes_100 = sum(payslips_mes_normal.mapped('line_ids').filtered(
                    lambda line: line.code in self.company_id.sueldos_y_jornales_report_codigos_hex_100
                ).mapped('total'))
                salario_beneficios_liquidaciones = sum(payslips_mes_liquidacion.mapped('line_ids').filtered(
                    lambda line: line.code in (self.company_id.sueldos_y_jornales_report_codigos_otros_beneficios or '').split(',') and
                                 line.code not in ['AGUIPR']
                ).mapped('total'))
                salario_aguinaldo_liquidaciones = sum(payslips_mes_liquidacion.mapped('line_ids').filtered(
                    lambda line: line.code in ['AGUIPR']
                ).mapped('total'))

                cantidad_horas_extra_mes_50 = 0
                cantidad_horas_extra_mes_100 = 0
                for payslip_mes in payslips_mes_normal:
                    if not payslip_mes.legacy_payslip_details:
                        payslip_mes_line_ids_hex50 = payslip_mes.line_ids.filtered(
                            lambda line: line.total and line.code in self.company_id.sueldos_y_jornales_report_codigos_hex_50
                        )
                        payslip_mes_line_ids_hex100 = payslip_mes.line_ids.filtered(
                            lambda line: line.total and line.code in self.company_id.sueldos_y_jornales_report_codigos_hex_100
                        )
                        cantidad_horas_extra_mes_50 += sum(payslip_mes_line_ids_hex50.mapped('quantity'))
                        cantidad_horas_extra_mes_100 += sum(payslip_mes_line_ids_hex100.mapped('quantity'))
                    else:
                        payslip_mes_worked_days_line_ids_hex50 = payslip_mes.mapped('worked_days_line_ids').filtered(
                            lambda line: line.work_entry_type_id.code in self.company_id.sueldos_y_jornales_report_codigos_hex_50
                        )
                        payslip_mes_worked_days_line_ids_hex100 = payslip_mes.mapped('worked_days_line_ids').filtered(
                            lambda line: line.work_entry_type_id.code in self.company_id.sueldos_y_jornales_report_codigos_hex_100
                        )
                        cantidad_horas_extra_mes_50 += sum(payslip_mes_worked_days_line_ids_hex50.mapped('number_of_hours'))
                        cantidad_horas_extra_mes_100 += sum(payslip_mes_worked_days_line_ids_hex100.mapped('number_of_hours'))

                total_horas_extras_50_cant += cantidad_horas_extra_mes_50
                total_horas_extras_100_cant += cantidad_horas_extra_mes_100

                total_horas_extras_50_monto += salario_horas_extra_mes_50
                total_horas_extras_100_monto += salario_horas_extra_mes_100
                total_liquidacion_beneficios_monto += salario_beneficios_liquidaciones
                total_aguinaldo += salario_aguinaldo_liquidaciones

                salario_mes -= salario_horas_extra_mes_50 + salario_horas_extra_mes_100 + salario_bonificacion_familiar
                total_bonificacion_familiar += salario_bonificacion_familiar
                total_salario += salario_mes

                rightAndWrite(cantidad_horas_mes, number)
                rightAndWrite(salario_mes, number)
            rightAndWrite(total_horas_extras_50_cant, number)
            rightAndWrite(total_horas_extras_50_monto, number)
            rightAndWrite(total_horas_extras_100_cant, number)
            rightAndWrite(total_horas_extras_100_monto, number)
            payslips_aguinaldo = self.get_payslips_aguinaldo(payslips)
            total_aguinaldo += sum(payslips_aguinaldo.mapped('line_ids').filtered(lambda line: line.code == 'AGUI').mapped('total'))
            rightAndWrite(total_aguinaldo, number)
            rightAndWrite(total_liquidacion_beneficios_monto, number)
            rightAndWrite(total_bonificacion_familiar, number)
            payslips_vacacion = self.get_payslips_vacacion(payslips)
            total_vacacion = sum(payslips_vacacion.mapped('line_ids').filtered(lambda line: line.code == 'GROSS').mapped('total'))
            rightAndWrite(total_vacacion, number)
            rightAndWrite(total_horas + total_horas_extras_50_cant + total_horas_extras_100_cant, number)
            rightAndWrite(total_salario, number)
            rightAndWrite(
                total_salario +
                total_horas_extras_50_monto +
                total_horas_extras_100_monto +
                total_aguinaldo +
                total_vacacion +
                total_bonificacion_familiar +
                total_liquidacion_beneficios_monto,
                number)

        workbook.close()

    def create_resumen_general_mtess_xlsx_file(self, dt):
        # os.chdir('/tmp')
        foldername = "Reportes EyO SyJ " + dt
        folderpath = foldername
        company_foldername = folderpath + "/" + self.company_id.name.replace("'", "")
        workbook = xlsxwriter.Workbook(
            company_foldername +
            '/Resumen General ' +
            str(self.year) +
            ' - ' +
            self.company_id.name.replace("'", "") +
            ' - ' +
            (self.company_id.nro_patronal or '') +
            '.xlsx'
        )
        global sheet
        global bold
        global number
        global date_only
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Datos'[:31])
        bold = workbook.add_format({'bold': True})
        number = workbook.add_format({'num_format': '0'})
        date_only = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        position_x = 0
        position_y = 0

        def addSalto():
            global position_x
            global position_y
            position_x = 0
            position_y += 1

        def addRight():
            global position_x
            position_x += 1

        def simpleWrite(to_write, format=None):
            global sheet
            if isinstance(to_write, int) or isinstance(to_write, float):
                to_write = int(to_write)
            sheet.write(position_y, position_x, to_write or ('' if type(to_write) != int else 0), format)

        def breakAndWrite(to_write, format=None):
            global sheet
            addSalto()
            simpleWrite(to_write, format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            simpleWrite(to_write, format)

        contracts = self.env['hr.contract.active_history'].search([
            ('contract_id', '!=', False),
            ('contract_id.employee_id', '!=', False),
            ('contract_id.company_id', '=', self.company_id.id),
        ]).filtered(lambda contract_active_history:
                    contract_active_history.date_start.year <= self.year and
                    (
                            not contract_active_history.date_end or
                            contract_active_history.date_end.year >= self.year
                    )
                    ).mapped('contract_id').sorted(
            key=lambda contract: ((contract.employee_id.apellido or ''), (contract.employee_id.nombre or ''))
        )

        simpleWrite('Nropatronal')
        rightAndWrite('anho')
        rightAndWrite('supjefesvarones')
        rightAndWrite('supjefesmujeres')
        rightAndWrite('empleadosvarones')
        rightAndWrite('empleadosmujeres')
        rightAndWrite('obrerosvarones')
        rightAndWrite('obrerosmujeres')
        rightAndWrite('menoresvarones')
        rightAndWrite('menoresmujeres')
        rightAndWrite('orden')
        for c in range(1, 6):
            breakAndWrite(self.company_id.nro_patronal)
            rightAndWrite(self.year, number)
            for employee_type in ['supervisor', 'empleado', 'obrero', 'menor']:
                if c == 1:
                    for gender in ['male', 'female']:
                        rightAndWrite(
                            len(contracts.mapped('employee_id').filtered(lambda x:
                                                                         x.gender == gender and
                                                                         x.mtess_report_employee_type == employee_type
                                                                         ))
                        )
                if c == 2:
                    for gender in ['male', 'female']:
                        cantidad_horas = 0
                        for contract in contracts.filtered(lambda x:
                                                           x.employee_id.gender == gender and
                                                           x.employee_id.mtess_report_employee_type == employee_type
                                                           ):
                            for month in range(1, 13):
                                for dia in range(1, get_monthrange(self.year, month) + 1):
                                    cantidad_hora = self.comprobar_dia(dia, month, contract)
                                    cantidad_horas += cantidad_hora if isinstance(cantidad_hora, int) else 0
                        rightAndWrite(cantidad_horas)
                if c == 3:
                    for gender in ['male', 'female']:
                        cantidad_sueldos_o_jornales = 0
                        for contract in contracts.filtered(lambda x:
                                                           x.employee_id.gender == gender and
                                                           x.employee_id.mtess_report_employee_type == employee_type
                                                           ):
                            cantidad_sueldos_o_jornales += sum(
                                self.env['hr.payslip'].search([
                                    ('state', 'in', ['done', 'paid']),
                                    ('contract_id', '=', contract.id),
                                ]).filtered(
                                    lambda payslip: payslip.date_from.year == self.year
                                ).mapped('line_ids').filtered(
                                    lambda line: line.code == 'GROSS'
                                ).mapped('total')
                            )
                        rightAndWrite(cantidad_sueldos_o_jornales, number)
                if c == 4:
                    for gender in ['male', 'female']:
                        cantidad_ingresos = len(contracts.filtered(lambda x:
                                                                   x.employee_id.gender == gender and
                                                                   x.employee_id.mtess_report_employee_type == employee_type and
                                                                   x.date_start.year == self.year
                                                                   ))
                        rightAndWrite(cantidad_ingresos)
                if c == 5:
                    for gender in ['male', 'female']:
                        cantidad_ingresos = len(contracts.filtered(lambda x:
                                                                   x.employee_id.gender == gender and
                                                                   x.employee_id.mtess_report_employee_type == employee_type and
                                                                   x.date_end and
                                                                   x.date_end.year == self.year
                                                                   ))
                        rightAndWrite(cantidad_ingresos)

            rightAndWrite(c, number)

        workbook.close()

    def action_print_eyo_xlsx_slow_mode(self):
        # reportes_ministerio_trabajo_py/report/reportes_ministerio_trabajo.py
        dt = str(datetime.datetime.today())
        return {
            'type': 'ir.actions.act_url',
            'url': '/reportes_ministerio_trabajo/slow_mode/reporte_xlsx_eyo?eyo_id=' + str(self.id) + '&dt=' + str(dt),
            'target': 'self',
        }

    def action_print_syj_xlsx_slow_mode(self):
        # reportes_ministerio_trabajo_py/report/reportes_ministerio_trabajo.py
        dt = str(datetime.datetime.today())
        return {
            'type': 'ir.actions.act_url',
            'url': '/reportes_ministerio_trabajo/slow_mode/reporte_xlsx_syj?eyo_id=' + str(self.id) + '&dt=' + str(dt),
            'target': 'self',
        }

    def action_print_rg_xlsx_slow_mode(self):
        # reportes_ministerio_trabajo_py/report/reportes_ministerio_trabajo.py
        dt = str(datetime.datetime.today())
        return {
            'type': 'ir.actions.act_url',
            'url': '/reportes_ministerio_trabajo/slow_mode/reporte_xlsx_rg?eyo_id=' + str(self.id) + '&dt=' + str(dt),
            'target': 'self',
        }


class SueldosYJornalesZIP(models.Model):
    _name = 'sueldos_y_jornales_zip_model'
    _description = 'Modelo auxiliar para la generación de reportes'

    wizard_id = fields.Many2one('reportes_ministerio_trabajo', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Compañía')
    month = fields.Selection(selection=[
        ('1', 'Enero'),
        ('2', 'Febrero'),
        ('3', 'Marzo'),
        ('4', 'Abril'),
        ('5', 'Mayo'),
        ('6', 'Junio'),
        ('7', 'Julio'),
        ('8', 'Agosto'),
        ('9', 'Setiembre'),
        ('10', 'Octubre'),
        ('11', 'Noviembre'),
        ('12', 'Diciembre'),
    ], required=True, string='Mes')
    year = fields.Integer(string='Año')
    report_date_start = fields.Date(compute='_get_report_date')
    report_date_end = fields.Date(compute='_get_report_date')

    def _get_report_date(self):
        for this in self:
            this.report_date_end = tools.datetime.strptime(
                str(this.year) + '-' + this.month + '-' + str(get_monthrange(this.year, int(this.month))),
                '%Y-%m-%d'
            ).date()
            this.report_date_start = this.report_date_end.replace(day=1)

    def comprobar_dia(self, dia, contract, force_check_active_contract=False):
        dia_datetime = datetime.datetime.strptime(str(self.year) + '-' + str(self.month) + '-' + str(dia), '%Y-%m-%d').date()
        if force_check_active_contract:
            if dia_datetime < contract.date_start or (contract.date_end and dia_datetime > contract.date_end):
                return 0
        if dia_datetime.weekday() == 6:
            return 'D'
        elif self.env['calendario.feriado'].check_feriado(dia_datetime):
            return 'F'
        elif self.env['notificacion.vacacion'].search([
            ('contract_id', '=', contract.id),
            ('state', '=', 'done'),
            ('fecha_inicio_vacaciones', '<=', dia_datetime),
            ('fecha_fin_vacaciones', '>=', dia_datetime)
        ]):
            return 'V'
        elif self.env['hr.leave'].search([
            ('holiday_status_id.appears_in_mtess_reports', '=', True),
            ('contract_id', '=', contract.id),
            ('state', '=', 'validate'),
            ('request_date_from', '<=', dia_datetime),
            ('request_date_to', '>=', dia_datetime),
            ('holiday_status_id.code', 'in', ['REP'])
        ]):
            return 'REP'
        elif self.env['hr.leave'].search([
            ('holiday_status_id.appears_in_mtess_reports', '=', True),
            ('state', '=', 'validate'),
            ('contract_id', '=', contract.id),
            ('holiday_status_id.code', 'in', [
                'AUS',
                'SUNP',
                'AMON',
            ]),
            ('request_date_from', '<=', dia_datetime),
            ('request_date_to', '>=', dia_datetime),
        ]):
            return 'A'
        elif dia_datetime < contract.date_start or (contract.date_end and dia_datetime > contract.date_end):
            return 0
        elif dia_datetime.weekday() == 5 and contract.company_id.sueldos_y_jornales_report_dias_sabado_valor and contract.company_id.sueldos_y_jornales_report_dias_sabado_valor != 'normal':
            return int(contract.company_id.sueldos_y_jornales_report_dias_sabado_valor)
        else:
            return 8

    def get_monthrange(self, year, month):
        return (calendar.monthrange(int(year), int(month)))[1]


class VacacionesZIP(models.Model):
    _name = 'vacaciones_zip_model'
    _description = 'Modelo auxiliar para la generación de reportes'

    wizard_id = fields.Many2one('reportes_ministerio_trabajo', required=True, ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Compañía')
    year = fields.Integer(string='Año')


class ReportesMinisterioTrabajoWizard(models.Model):
    _name = 'reportes_ministerio_trabajo'
    _description = 'Wizard para el reportes del MJT (Empleados y Obreros, Sueldos y Jornales)'

    company_ids = fields.Many2many('res.company', string="Compañias", required=True, default=lambda self: self.env.companies)
    year = fields.Integer(string='Año', required=True, default=lambda self: fields.Date.today().year - 1)

    wizard_report_type = fields.Selection([('pdf', 'PDF'), ('xlsx', 'XLSX'), ])

    empleados_y_obreros_ids = fields.One2many('empleados_y_obreros_zip_model', 'wizard_id')
    empleados_y_obreros_count = fields.Integer(compute='_get_empleados_y_obreros_count')

    sueldos_y_jornales_ids = fields.One2many('sueldos_y_jornales_zip_model', 'wizard_id')
    sueldos_y_jornales_count = fields.Integer(compute='_get_sueldos_y_jornales_count')

    vacaciones_ids = fields.One2many('vacaciones_zip_model', 'wizard_id')
    vacaciones_count = fields.Integer(compute='_get_vacaciones_count')

    def download_reports_pdf(self, **kw):
        dt = str(datetime.datetime.today())
        if request.env.user.has_group('hr.group_hr_manager'):
            mtess_reports_slow_server_mode = self.env['ir.config_parameter'].sudo().get_param('mtess_reports_slow_server_mode') == 'True'
            self.wizard_report_type = 'pdf'
            self.search([
                ('id', '!=', self.id),
                ('wizard_report_type', '=', self.wizard_report_type),
                ('year', '=', self.year),
            ]).filtered(lambda x: x.company_ids == self.company_ids).unlink()
            values = {
                'cids': str(','.join([str(company.id) for company in self.company_ids])),
                'year': str(self.year),
                'month': '12',
                'dt': str(dt),
                'wizard_id': str(self.id),
            }
            if not mtess_reports_slow_server_mode:
                result = {
                    'type': 'ir.actions.act_url',
                    'url': '/reportes_ministerio_trabajo/reportes_eyo_syj_zip?'
                           'cids=' + values.get('cids') +
                           '&year=' + values.get('year') +
                           '&month=' + values.get('month') +
                           '&dt=' + values.get('dt') +
                           '&wizard_id=' + values.get('wizard_id'),
                    'target': 'self',
                }
            else:
                addons.reportes_ministerio_trabajo_py.controllers.controllers.ReportesEyOSyJZIP.download_empleados_obreros_report(self=self, kw_aux=values)
                result = {
                    'type': 'ir.actions.act_window',
                    'name': 'reportes_ministerio_trabajo_pdf_slow_mode_action',
                    'view_mode': 'form',
                    'res_model': 'reportes_ministerio_trabajo',
                    'res_id': self.id,
                    'views': [(self.env.ref('reportes_ministerio_trabajo_py.reportes_ministerio_trabajo_slow_mode_form').id, 'form')],
                    'target': 'current',
                }

            return result
        else:
            return werkzeug.utils.redirect('/web/login')

    def download_reports_xlsx(self, **kw):
        dt = str(datetime.datetime.today())

        if request.env.user.has_group('hr.group_hr_manager'):
            mtess_reports_slow_server_mode = self.env['ir.config_parameter'].sudo().get_param('mtess_reports_slow_server_mode') == 'True'
            self.wizard_report_type = 'xlsx'
            self.search([
                ('id', '!=', self.id),
                ('wizard_report_type', '=', self.wizard_report_type),
                ('year', '=', self.year),
            ]).filtered(lambda x: x.company_ids == self.company_ids).unlink()

            self.env.cr.execute(
                'select res_company_id from reportes_ministerio_trabajo_res_company_rel where reportes_ministerio_trabajo_id = ' + str(
                    self.id))
            companias = [str(x[0]) for x in self.env.cr.fetchall()]

            values = {
                'cids': str(','.join(companias)),
                'year': str(self.year),
                'month': '12',
                'dt': str(dt),
                'wizard_id': str(self.id),
            }
            if not mtess_reports_slow_server_mode:
                result = {
                    'type': 'ir.actions.act_url',
                    'url': '/reportes_ministerio_trabajo/reportes_eyo_syj_zip_xlsx?'
                           'cids=' + values.get('cids') +
                           '&year=' + values.get('year') +
                           '&month=' + values.get('month') +
                           '&dt=' + values.get('dt') +
                           '&wizard_id=' + values.get('wizard_id'),
                    'target': 'self',
                }
            else:
                addons.reportes_ministerio_trabajo_py.controllers.controllers.ReportesEyOSyJZIP.download_mtess_report_xlsx(self=self, kw_aux=values)
                result = {
                    'type': 'ir.actions.act_window',
                    'name': 'reportes_ministerio_trabajo_xlsx_slow_mode_action',
                    'view_mode': 'form',
                    'res_model': 'empleados_y_obreros_zip_model',
                    'res_id': self.empleados_y_obreros_ids.id,
                    'views': [(self.env.ref('reportes_ministerio_trabajo_py.empleados_y_obreros_slow_mode_form_view').id, 'form')],
                    'target': 'current',
                }

            return result

        else:
            return werkzeug.utils.redirect('/web/login')

    def _get_empleados_y_obreros_count(self):
        for this in self:
            this.empleados_y_obreros_count = len(this.empleados_y_obreros_ids)

    def action_open_empleados_y_obreros(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Empleados y Obreros',
            'res_model': 'empleados_y_obreros_zip_model',
            'res_ids': self.empleados_y_obreros_ids.ids,
            'domain': "[('wizard_id', '=', %s)]" % self.id,
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
        }

    def _get_sueldos_y_jornales_count(self):
        for this in self:
            this.sueldos_y_jornales_count = len(this.sueldos_y_jornales_ids)

    def action_open_sueldos_y_jornales(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sueldos y Jornales',
            'res_model': 'sueldos_y_jornales_zip_model',
            'res_ids': self.sueldos_y_jornales_ids.ids,
            'domain': "[('wizard_id', '=', %s)]" % self.id,
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
        }

    def _get_vacaciones_count(self):
        for this in self:
            this.vacaciones_count = len(this.vacaciones_ids)

    def action_open_vacaciones(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Vacaciones',
            'res_model': 'vacaciones_zip_model',
            'res_ids': self.vacaciones_ids.ids,
            'domain': "[('wizard_id', '=', %s)]" % self.id,
            'view_mode': 'tree,form',
            'target': 'current',
            'context': self.env.context,
        }
