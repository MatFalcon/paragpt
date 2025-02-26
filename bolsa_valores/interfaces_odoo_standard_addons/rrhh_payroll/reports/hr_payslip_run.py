from odoo import api, fields, models


class HrPayslipRunReportXLSX(models.AbstractModel):
    _name = 'report.rrhh_payroll.hr_payslip_run_report_xlsx_t'
    _inherit = 'report.report_xlsx.abstract'

    def print_custom_columns_headers(self, payslip_run_ids):
        # rrhh_payroll/reports/hr_payslip_run.py
        # Con esta función se pueden anexar columnas pesonalizadas dependiendo de las necesidades del cliente
        # Se debe de retornar un array con los valores a imprimir en las cabeceras. IE: ['Cabecera 1','Cabecera 2','Cabecera 3']
        return []

    def print_custom_columns_content(self, payslip_run_ids, payslip):
        # rrhh_payroll/reports/hr_payslip_run.py
        # Con esta función se pueden anexar columnas pesonalizadas dependiendo de las necesidades del cliente
        # Se debe de retornar un array con los valores a imprimir en las líneas del reporte.
        # Se tiene a mano la variable payslip, de donde se p[ueden quitar datos del contrato, empleado, lote y hasta la propia nómina.
        # Se debe de retornar un array con los valores a imprimir en la línea del reporte, debe de ser un array de la misma longitud que las cabeceras declaradas. IE: ['Valor 1','Valor 2','Valor 3']
        return []

    def generate_xlsx_report(self, workbook, data, payslip_run_ids):
        global sheet
        global bold
        global num_format
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Líneas de salarios')
        bold = workbook.add_format({'bold': True})
        numerico = workbook.add_format({'num_format': True, 'align': 'right'})
        numerico.set_num_format('#,##0')
        numerico_total = workbook.add_format({'num_format': True, 'align': 'right', 'bold': True})
        numerico_total.set_num_format('#,##0')
        wrapped_text = workbook.add_format()
        wrapped_text.set_text_wrap()
        wrapped_text_bold = workbook.add_format({'bold': True})
        wrapped_text_bold.set_text_wrap()

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

        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 50, 20)

        report_concepts = self.env['hr.payslip.run.report_concept'].search([])

        simpleWrite('Cédula', bold)
        rightAndWrite('Empleado', bold)
        rightAndWrite('Fecha de Ingreso', bold)
        rightAndWrite('Fecha de Egreso', bold)
        rightAndWrite('Departamento', bold)
        rightAndWrite('Puesto de Trabajo', bold)
        rightAndWrite('Etiquetas', bold)
        rightAndWrite('Nombre del Lote', bold)
        rightAndWrite('Salario Mensual', bold)
        rightAndWrite('Salario Jornal', bold)
        rightAndWrite('Salario Hora', bold)
        rightAndWrite('Dias a trabajar', bold)

        for custom_header in self.print_custom_columns_headers(payslip_run_ids):
            rightAndWrite(custom_header, bold)

        for report_concept in report_concepts:
            rightAndWrite(report_concept.title, bold)
        for payslip in payslip_run_ids.slip_ids.sorted(key=lambda x: x.employee_id.name):
            breakAndWrite(payslip.employee_id.identification_id)
            rightAndWrite(payslip.employee_id.name)
            rightAndWrite(payslip.contract_id.date_start.strftime('%d/%m/%Y') if payslip.contract_id.date_start else '')
            rightAndWrite(payslip.contract_id.date_end.strftime('%d/%m/%Y') if payslip.contract_id.date_end else '')
            rightAndWrite(payslip.contract_id.department_id.name or '')
            rightAndWrite(payslip.employee_id.job_id.name or '')
            rightAndWrite(', '.join(category.name for category in payslip.employee_id.category_ids) if payslip.employee_id.category_ids else '')
            rightAndWrite(payslip.payslip_run_id.name)
            rightAndWrite(payslip.contract_id.wage if payslip.contract_id.wage_type == 'monthly' else '', numerico)
            rightAndWrite(payslip.contract_id.daily_wage if payslip.contract_id.wage_type == 'daily' else '', numerico)
            rightAndWrite(payslip.contract_id.hourly_wage if payslip.contract_id.wage_type == 'hourly' else '', numerico)
            rightAndWrite(payslip.contract_id.number_of_planned_work_days if payslip.contract_id.wage_type == 'daily' else '')

            for custom_content in self.print_custom_columns_content(payslip_run_ids, payslip):
                rightAndWrite(custom_content)

            for report_concept in report_concepts:
                rightAndWrite(sum([
                    line.total for line in payslip.line_ids.filtered(
                        lambda line: line.salary_rule_id.code in report_concept.elements.split(',')
                    )
                ]), numerico)
