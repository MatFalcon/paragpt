# -*- coding: utf-8 -*-
import odoo
from odoo import models, fields, api, exceptions, _


class ReporteVacacionesWizard(models.TransientModel):
    _name = 'reporte_vacaciones_wizard'
    _description = "Wizard: Rápida generación de los reportes de las vacaciones"

    year = fields.Integer(string='Año', required=True)
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

    def get_mes(self, mes):
        # rrhh_payroll/reports/reporte_vacaciones.py
        return odoo.addons.rrhh_payroll.models.wizard_generar_nominas.get_mes(mes)

    def print_report(self):
        # rrhh_payroll/reports/reporte_vacaciones.py
        return self.env.ref('rrhh_payroll.reporte_vacaciones').report_action(self)


class ReporteVacacionesXLSX(models.AbstractModel):
    _name = 'report.rrhh_payroll.reporte_vacaciones_t'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, wizard):
        # rrhh_payroll/reports/reporte_vacaciones.py
        global sheet
        global bold
        global num_format
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Vacaciones')
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

        sheet.set_column(0, 0, 15)
        sheet.set_column(2, 2, 15)
        sheet.set_column(4, 7, 15)
        sheet.set_column(1, 1, 30)
        sheet.set_column(3, 3, 30)

        vacaciones = self.env['notificacion.vacacion'].search([('state', '=', 'done')]).filtered(
            lambda x: x.fecha_inicio_vacaciones.month == int(wizard.month) and x.fecha_inicio_vacaciones.year == int(
                wizard.year))

        simpleWrite('Informe de Vacaciones ' + wizard.get_mes(int(wizard.month)) + ' ' + str(wizard.year), bold)
        breakAndWrite('C.I. Patron', bold)
        rightAndWrite('Nombre Patron', bold)
        rightAndWrite('CI Empleado', bold)
        rightAndWrite('Nombre Empleado', bold)
        rightAndWrite('Primer Día', bold)
        rightAndWrite('Último Día', bold)
        rightAndWrite('Monto', bold)
        rightAndWrite('Descuento IPS', bold)

        if not vacaciones:
            addSalto()
            addSalto()
            breakAndWrite('No existen datos para el periodo seleccionado')
        else:
            for vacacion in vacaciones:
                breakAndWrite(
                    vacacion.contract_id.company_id.vat.split('-')[0] if vacacion.contract_id.company_id.vat else '')
                rightAndWrite(vacacion.contract_id.company_id.nombre + ' ' + vacacion.contract_id.company_id.apellido)
                rightAndWrite(vacacion.employee_id.identification_id)
                rightAndWrite(vacacion.employee_id.name)
                rightAndWrite(str(vacacion.fecha_inicio_vacaciones.strftime('%d/%m/%Y')))
                rightAndWrite(str(vacacion.fecha_fin_vacaciones.strftime('%d/%m/%Y')))
                rightAndWrite(
                    round(sum(vacacion.payslip_id.line_ids.filtered(lambda x: x.code in ['GROSS']).mapped('total'))))
                rightAndWrite(
                    round(sum(
                        vacacion.payslip_id.line_ids.filtered(lambda x: x.code in ['IPS', 'AMH']).mapped('total'))))
