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

    def generate_xlsx_report(self, workbook, uno, payslip_run):
        global sheet
        global bold
        global position_x
        global position_y
        sheet = workbook.add_worksheet('datos')
        bold = workbook.add_format({'bold': True})
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

        def breakAndWrite(to_write, format=None):
            global sheet
            addSalto()
            sheet.write(position_y, position_x, to_write, format)

        def simpleWrite(to_write, format=None):
            global sheet
            sheet.write(position_y, position_x, to_write, format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            sheet.write(position_y, position_x, to_write, format)

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
        txt_ips_rei = ''
        for payslip in payslip_run.slip_ids:
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
            contenido = ''
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 10, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna E
            contenido = int(payslip.employee_id.identification_id.replace('.', '').replace(',', '').replace(' ', '')) \
                if payslip.employee_id.identification_id else ''
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 10, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna F
            contenido = payslip.employee_id.apellido
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 30, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna G
            contenido = payslip.employee_id.nombre
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 30, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna H
            contenido = 'E'
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 1, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna I
            dias_laborales = sum(
                payslip.worked_days_line_ids.filtered(lambda x: x.code in ['WORK100']).mapped('number_of_days')
            )
            dias_ausencia = sum([
                int(worked_day_line.number_of_days)
                for worked_day_line in
                payslip.worked_days_line_ids.filtered(
                    lambda x: x.code in payslip.env['hr.leave.type'].search([]).mapped('code'))
            ])
            contenido = int(dias_laborales - dias_ausencia)
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 2, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna J
            payslip_net = sum(payslip.line_ids.filtered(lambda line: line.code in ['GROSS']).mapped('total'))
            contenido = payslip_net
            rightAndWrite(contenido)
            contenido, campo_size, campo_relleno = str(contenido), 10, ' '
            txt_ips_rei += contenido.rjust(campo_size, campo_relleno) if len(contenido) <= campo_size else 'error'

            # Columna K
            fecha = payslip.date_from
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
            contenido = payslip_net
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
