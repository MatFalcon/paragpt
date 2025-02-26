# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def imprimir_reporte_ips_rei(self):
        return self.env.ref('ips_rei_hr_payslip.ips_rei_action_xlsx').report_action(self)


class PartnerXlsx(models.AbstractModel):
    _name = 'report.ips_rei_hr_payslip.xlsx_report'
    _inherit = 'report.report_xlsx.abstract'

    def get_monto_ausencia(self, payslip_employee):
        return sum([
            line_id.total
            for line_id in
            payslip_employee.line_ids.filtered(
                lambda x: x.code in self.env['hr.leave.type'].search([]).mapped('code'))
        ])

    def get_payslip_gross(self, payslip_employee):
        payslip_gross = int(sum(payslip_employee.line_ids.filtered(lambda line: line.code in ['GROSS']).mapped('total')))
        return payslip_gross

    def get_payslip_basic_quantity(self, payslip_employee):
        if payslip_employee.legacy_payslip_details:
            return sum(
                payslip_employee.worked_days_line_ids.filtered(lambda line: line.code in ['WORK100']).mapped('number_of_days')
            )
        return sum(
            payslip_employee.line_ids.filtered(lambda line: line.total and line.category_id.code in ['BASIC']).mapped('quantity')
        )

    def get_payslip_leave_quantity(self, payslip_employee):
        dias_ausencia = sum([
            line.quantity if line.total else 0
            for line in
            payslip_employee.line_ids.filtered(
                lambda x: (x.code if not payslip_employee.legacy_payslip_details else x.salary_rule_id.code) in self.env['hr.leave.type'].search([]).mapped(
                    'code')
            )
        ])
        if payslip_employee.struct_id.type_id.structure_type_tag == 'vacacion':
            dias_ausencia = -dias_ausencia
        return dias_ausencia

    def generate_xlsx_report(self, workbook, uno, payslip_run):
        global sheet
        global bold
        global position_x
        global position_y
        sheet = workbook.add_worksheet('datos')
        bold = workbook.add_format({'bold': True})
        position_x = 0
        position_y = 0

        def change_characters(text):
            allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,1234567890'
            for character_pair in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ñ', 'n')]:
                text = text.replace(character_pair[0], character_pair[1])
                text = text.replace(character_pair[0].upper(), character_pair[1].upper())
            for character in text:
                if character not in allowed_characters:
                    text = text.replace(character, ' ')
            return text

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
            if isinstance(to_write, str):
                to_write = change_characters(to_write)
            sheet.write(position_y, position_x, to_write, format)

        def breakAndWrite(to_write, format=None):
            global sheet
            addSalto()
            simpleWrite(to_write, format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            simpleWrite(to_write, format)

        # simpleWrite('Nro. Patronal', bold)
        sheet.merge_range('A1:C1', 'Nro. Patronal', bold)
        addRight()
        addRight()
        rightAndWrite('Nro. Asegurado', bold)
        rightAndWrite('C.I.N°', bold)
        rightAndWrite('Apellido', bold)
        rightAndWrite('Nombre', bold)
        rightAndWrite('Categoria', bold)
        rightAndWrite('Días Trab.', bold)
        rightAndWrite('Salario Imponible', bold)
        rightAndWrite('MesAño de Pago', bold)
        rightAndWrite('Cod. Actividad', bold)
        rightAndWrite('Salario Real', bold)

        addSalto()
        nro_patronal = payslip_run.company_id.nro_ips.replace('.', '').replace('-', '').replace(' ', '')
        p_nro_patronal = s_nro_patronal = t_nro_patronal = ''
        c = 0
        for i in reversed(nro_patronal):
            if c > 5:
                p_nro_patronal = i + p_nro_patronal
            elif c > 3:
                s_nro_patronal = i + s_nro_patronal
            else:
                t_nro_patronal = i + t_nro_patronal
            c += 1
        payslips = payslip_run.slip_ids.filtered(lambda x: x.state in ['done', 'paid'] and x.contract_id.seguro_ips)
        txt_ips_rei = ''
        for employee_id in payslips.mapped('employee_id'):
            payslips_employee = payslips.filtered(lambda x: x.employee_id == employee_id)
            if not payslips_employee:
                continue
            # if employee_id.id != 1:
            #     continue

            # Columna A
            contenido = p_nro_patronal
            simpleWrite(int(contenido or 0))
            contenido, campo_size, campo_relleno = str(contenido), 4, '0'
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna B
            contenido = s_nro_patronal
            rightAndWrite(int(contenido or 0))
            contenido, campo_size, campo_relleno = str(contenido), 2, '0'
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna C
            contenido = t_nro_patronal
            rightAndWrite(int(contenido or 0))
            contenido, campo_size, campo_relleno = str(contenido), 4, '0'
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna D
            employee_nro_cedula = int(employee_id.identification_id.replace('.', '').replace(',', '').replace(' ', '')) \
                if employee_id.identification_id else ''
            contenido = employee_nro_cedula
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 10, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna E
            contenido = employee_nro_cedula
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 10, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna F
            contenido = employee_id.apellido
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 30, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna G
            contenido = employee_id.nombre
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 30, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna H
            contenido = 'E'
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 1, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna I
            total_dias = 0
            for payslip_employee in payslips_employee:
                dias_laborales = self.get_payslip_basic_quantity(payslip_employee)
                dias_ausencia = self.get_payslip_leave_quantity(payslip_employee)
                total_dias += round(dias_laborales - dias_ausencia)

            contenido = total_dias
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 2, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna J
            payslip_gross = 0
            for payslip_employee in payslips_employee:
                monto_ausencia = self.get_monto_ausencia(payslip_employee)
                payslip_gross += self.get_payslip_gross(payslip_employee)
                payslip_gross -= sum(payslip_employee.line_ids.filtered(
                    lambda x: x.code in payslip_employee.contract_id.company_id.sueldos_y_jornales_report_codigos_bonificacion_familiar).mapped('total'))
                if payslip_employee.struct_id.type_id.structure_type_tag != 'vacacion':
                    payslip_gross -= monto_ausencia

            contenido = payslip_gross
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 10, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna K
            fecha = min(payslip_employee.date_from for payslip_employee in payslips_employee)
            contenido = int(str(fecha.month) + str(fecha.year))
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 6, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna L
            contenido = ''
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 2, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna M
            contenido = payslip_gross
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 10, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            addSalto()
            txt_ips_rei += '\n'

        sheet2 = workbook.add_worksheet('Grabar datos')
        # formula = '''
        # =CONCATENATE(
        #     IF(
        #         LEN(
        #             $datos.A%line
        #         ) <= 4,
        #         (            CONCATENATE(
        #                 REPT(
        #                     "0",
        #                     ( 4 -
        #                         LEN(
        #                             $datos.A%line
        #                         ) )
        #                 ),
        #                 $datos.A%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.B%line
        #         ) <= 2,
        #         (            CONCATENATE(
        #                 REPT(
        #                     "0",
        #                     ( 2 -
        #                         LEN(
        #                             $datos.B%line
        #                         ) )
        #                 ),
        #                 $datos.B%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.C%line
        #         ) <= 4,
        #         (            CONCATENATE(
        #                 REPT(
        #                     "0",
        #                     ( 4 -
        #                         LEN(
        #                             $datos.C%line
        #                         ) )
        #                 ),
        #                 $datos.C%line
        #             ) ),
        #         IF(
        #             LEN(
        #                 $datos.C%line
        #             ) = 5,
        #             $datos.C%line,
        #             "error"
        #         )
        #     ),
        #     IF(
        #         LEN(
        #             $datos.D%line
        #         ) <= 10,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 10 -
        #                         LEN(
        #                             $datos.D%line
        #                         ) )
        #                 ),
        #                 $datos.D%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.E%line
        #         ) <= 10,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 10 -
        #                         LEN(
        #                             $datos.E%line
        #                         ) )
        #                 ),
        #                 $datos.E%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.F%line
        #         ) <= 30,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 30 -
        #                         LEN(
        #                             $datos.F%line
        #                         ) )
        #                 ),
        #                 $datos.F%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.G%line
        #         ) <= 30,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 30 -
        #                         LEN(
        #                             $datos.G%line
        #                         ) )
        #                 ),
        #                 $datos.G%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.H%line
        #         ) <= 1,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 1 -
        #                         LEN(
        #                             $datos.H%line
        #                         ) )
        #                 ),
        #                 $datos.H%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.I%line
        #         ) <= 2,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 2 -
        #                         LEN(
        #                             $datos.I%line
        #                         ) )
        #                 ),
        #                 $datos.I%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.J%line
        #         ) <= 10,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 10 -
        #                         LEN(
        #                             $datos.J%line
        #                         ) )
        #                 ),
        #                 $datos.J%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.K%line
        #         ) <= 6,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 6 -
        #                         LEN(
        #                             $datos.K%line
        #                         ) )
        #                 ),
        #                 $datos.K%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.L%line
        #         ) <= 2,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 2 -
        #                         LEN(
        #                             $datos.L%line
        #                         ) )
        #                 ),
        #                 $datos.L%line
        #             ) ),
        #         "error"
        #     ),
        #     IF(
        #         LEN(
        #             $datos.M%line
        #         ) <= 10,
        #         (            CONCATENATE(
        #                 REPT(
        #                     " ",
        #                     ( 10 -
        #                         LEN(
        #                             $datos.M%line
        #                         ) )
        #                 ),
        #                 $datos.M%line
        #             ) ),
        #         "error"
        #     )
        # )
        #             '''

        # for c, payslip in enumerate(payslip_run.slip_ids):
        #     sheet2.write_formula('A' + str(c + 1), formula.replace('%line', str(c + 2)))

        position_x = 0
        position_y = -1
        sheet = sheet2
        for c, line in enumerate(txt_ips_rei.split('\n')):
            breakAndWrite(line)
