from odoo import api, fields, models
import datetime
from calendar import monthrange


class HrPaylslipRunReportConceptWiz(models.Model):
    _name = 'hr.payslip.run.report_concept_wiz'
    _description = 'Wizard para definir los elemenos para los reportes mensuales de nóminas'

    element_ids = fields.One2many('hr.payslip.run.report_concept', 'wizard_id', string='Elementos del Reporte de Salarios',
                                  default=lambda self: self.obtener_elementos_actuales(), relation='wizard_payslip_run_concept_rel')

    def obtener_elementos_actuales(self):
        return self.env['hr.payslip.run.report_concept'].search([])

    def button_actualizar_elementos(self):
        self.env['hr.payslip.run.report_concept'].search([('id', 'not in', self.element_ids.ids)]).unlink()
        for concept in self.env['hr.payslip.run.report_concept'].search([]):
            concept.elements = concept.elements.replace(' ', '')


class hrpaylsliprunreportconcept(models.Model):
    _name = 'hr.payslip.run.report_concept'
    _order = 'sequence asc,id asc'

    wizard_id = fields.Many2one('hr.payslip.run.report_concept_wiz')
    sequence = fields.Integer(default=9999)
    title = fields.Char('Título', required=True)
    elements = fields.Char('Conceptos', help='Códigos de las reglas salariales separadas por comas', required=True)
