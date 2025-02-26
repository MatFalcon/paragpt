# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class HrContracActivetHistoryWizard(models.TransientModel):
    _name = 'hr.contract.active_history.wizard'
    _description = 'Wizard para el reporte de Empleados Activos'
    companies_ids = fields.Many2many('res.company', string="Compañias")
    report_type = fields.Selection([('simple', 'Simple'), ('full', 'Completo')], string='Tipo de Reporte',
                                   default='simple', required=True)
    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)

    def print_report_pdf(self):
        return self.env.ref('reportes_ministerio_trabajo_py.report_contract_h_pdf').report_action(self)

    def print_report_xlsx(self):
        return self.env.ref('reportes_ministerio_trabajo_py.report_contract_h_xlsx').report_action(self)


class HrContractActiveHistoryReport(models.AbstractModel):
    _name = 'report.reportes_ministerio_trabajo_py.report_contract_h_pdf_t'
    _description = 'Reporte de Empleados Activos'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['hr.contract.active_history.wizard'].browse(docids)
        contract_histories = self.env['hr.contract.active_history']
        companies_ids = docs.companies_ids or self.env['res.company'].search([('active', 'in', [True, False])])
        contracts = contract_histories.get_contracts(company_ids=companies_ids, date_from=docs.date_from,
                                                     date_to=docs.date_to).sorted(
            key=lambda x: x.employee_id.name)
        return {
            'docs': docs,
            'contracts': contracts,
            'companies_ids': companies_ids,
        }


class HrContractActiveHistoryReportXLSX(models.AbstractModel):
    _name = 'report.reportes_ministerio_trabajo_py.report_contract_h_xlsx_t'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, report_wizard):
        global sheet
        global bold
        global number
        global date_only
        global position_x
        global position_y
        bold = workbook.add_format({'bold': True})
        number = workbook.add_format({'num_format': '0'})
        date_only = workbook.add_format({'num_format': 'yyyy-mm-dd'})

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
            sheet.write(position_y, position_x, to_write or '', format)

        def simpleWrite(to_write, format=None):
            global sheet
            sheet.write(position_y, position_x, to_write or ('' if type(to_write) != int else 0), format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            sheet.write(position_y, position_x, to_write or ('' if type(to_write) != int else 0), format)

        companies_ids = report_wizard.mapped('companies_ids') or self.env['res.company'].search(
            [('active', 'in', [True, False])])

        contracts = self.env['hr.contract.active_history'].get_contracts(company_ids=companies_ids,
                                                                  date_from=report_wizard.date_from,
                                                                  date_to=report_wizard.date_to).sorted(
            key=lambda x: x.employee_id.name)
        if report_wizard.report_type == 'full':
            for company in companies_ids:
                company_contracts = contracts.filtered(lambda x: x.company_id == company)
                if company_contracts:
                    sheet = workbook.add_worksheet(company.name[:31])
                    position_x = 0
                    position_y = 0
                    sheet.set_column(0, 3, 35)

                    simpleWrite('Empleados activos', bold)
                    breakAndWrite('Patrón:', bold)
                    rightAndWrite(company.name)
                    breakAndWrite('Empleados Activos entre las fechas:', bold)
                    rightAndWrite(report_wizard.date_from, date_only)
                    rightAndWrite(report_wizard.date_to, date_only)
                    addSalto()
                    breakAndWrite('Empleado', bold)
                    rightAndWrite('Fecha Inicio', bold)
                    rightAndWrite('Fecha Fin', bold)
                    rightAndWrite('Cuenta Corriente', bold)
                    for contract in company_contracts:
                        breakAndWrite(contract.employee_id.name)
                        rightAndWrite(contract.date_start, date_only)
                        rightAndWrite(contract.date_end, date_only)
                    addSalto()
                    breakAndWrite('Total empleados activos:', bold)
                    rightAndWrite(len(company_contracts))
            for company in companies_ids:
                company_contracts = contracts.filtered(lambda x: x.company_id == company)
                if not company_contracts:
                    sheet = workbook.add_worksheet(company.name[:31])
                    position_x = 0
                    position_y = 0

                    simpleWrite('Empleados activos', bold)
                    breakAndWrite('Patrón:', bold)
                    rightAndWrite(company.name)
                    breakAndWrite('Empleados Activos entre las fechas:', bold)
                    rightAndWrite(report_wizard.date_from, date_only)
                    rightAndWrite(report_wizard.date_to, date_only)
                    addSalto()
                    addSalto()
                    simpleWrite('No existen empleados activos en la fecha especificada', bold)
        if report_wizard.report_type == 'simple':
            sheet = workbook.add_worksheet('Empleados Activos')
            position_x = 0
            position_y = 0
            sheet.set_column(0, 3, 35)

            simpleWrite('Empleados activos', bold)
            breakAndWrite('Empleados Activos entre las fechas:', bold)
            rightAndWrite(report_wizard.date_from, date_only)
            rightAndWrite(report_wizard.date_to, date_only)
            addSalto()
            breakAndWrite('Empleador', bold)
            rightAndWrite('Nro de empleados Activos', bold)
            for company_id in companies_ids.filtered(lambda x: x in contracts.mapped('company_id')):
                breakAndWrite(company_id.name)
                rightAndWrite(len(contracts.filtered(lambda contract: contract.company_id == company_id)))
            for company_id in companies_ids.filtered(lambda x: x not in contracts.mapped('company_id')):
                breakAndWrite(company_id.name)
                rightAndWrite('No existen empleados activos en para el periodo selecionado')
