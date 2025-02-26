from odoo import fields, api, models, exceptions, tools
import datetime, logging

_logger = logging.getLogger(__name__)


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    structure_type_tag = fields.Selection([
        ('normal', 'Normal'),
        ('vacacion', 'Vacación'),
        ('aguinaldo', 'Aguinaldo'),
    ], string='Etiqueta del Tipo de Estructura', related='struct_id.structure_type_tag')
    computed_daily_wage = fields.Float(string='Salario Diario', compute='get_computed_daily_wage')
    legacy_payslip_details = fields.Boolean()

    def get_computed_daily_wage(self):
        # rrhh_payroll/models/hr_payslip.py
        for this in self:
            this.computed_daily_wage = this.contract_id.get_computed_daily_wage(this.date_to)

    @api.onchange('contract_id')
    def set_default_struct_id(self):
        struct_id = False
        if self.contract_id and self.contract_id.structure_id:
            struct_id = self.contract_id.structure_id
        self.struct_id = struct_id

    def get_dia_laboral(self, date):
        # reportes_ministerio_trabajo_py/models/hr_payslip.py
        return 1
        # Más cálculos en el módulo rrhh_payroll

    def get_bruto_para_aguinaldo(self):
        # reportes_ministerio_trabajo_py/models/hr_payslip.py
        return (
                sum(self.line_ids.filtered(lambda x: x.code in ['GROSS']).mapped('total')) -
                sum(self.line_ids.filtered(
                    lambda x: x.code in self.contract_id.company_id.base_aguinaldo_descuentos.split(',')).mapped('total'))
        )

    def crear_historial_salario(self):
        # reportes_ministerio_trabajo_py/models/hr_payslip.py
        for this in self:
            self.env['historial.salario'].search([('payslip_id', '=', this.id), ('state', '=', 'good')]).write({'state': 'bad'})
            self.env['historial.salario'].search([('state', '=', 'bad')]).unlink()
            if this.state in ['done', 'paid']:
                years = {}
                date_aux = this.date_from
                while date_aux <= this.date_to:
                    if not years.get(date_aux.year):
                        years[date_aux.year] = {}
                    if not years[date_aux.year].get(date_aux.month):
                        years[date_aux.year][date_aux.month] = {
                            'date_from': date_aux,
                            'days': 0,
                        }

                    years[date_aux.year][date_aux.month]['days'] += this.get_dia_laboral(date_aux)
                    years[date_aux.year][date_aux.month]['date_to'] = date_aux
                    date_aux += datetime.timedelta(days=1)
                days_total = sum(sum(month.get('days') for month in year.values()) for year in years.values())
                bruto_para_aguinaldo = this.get_bruto_para_aguinaldo()
                real_wage = (sum(this.line_ids.filtered(lambda x: x.code in ['GROSS']).mapped('total')))
                real_wage -= (sum(this.line_ids.filtered(
                    lambda x: x.code in this.contract_id.company_id.sueldos_y_jornales_report_codigos_bonificacion_familiar
                ).mapped('total')))
                # vacaciones_amount = (sum(this.line_ids.filtered(lambda x: x.code in ['VAC']).mapped('total')))
                # if not this.struct_id.type_id.structure_type_tag == 'vacacion':
                #     real_wage -= vacaciones_amount
                for year in years.values():
                    for month in year.values():
                        data = {
                            'state': 'good',
                            'date_from': month.get('date_from'),
                            'date_to': month.get('date_to'),
                            'real_wage': real_wage / days_total * month.get('days'),
                            'bruto_para_aguinaldo': bruto_para_aguinaldo / days_total * month.get('days'),
                            'payslip_id': this.id
                        }
                        self.env['historial.salario'].create(data)

    def action_payslip_done(self):
        # reportes_ministerio_trabajo/models/hr_payslip.py
        r = super(HrPayslip, self).action_payslip_done()
        self.crear_historial_salario()
        return r

    def action_payslip_cancel(self):
        # reportes_ministerio_trabajo/models/hr_payslip.py
        self.write({'state': 'cancel'})
        self.mapped('payslip_run_id').action_close()
        self.crear_historial_salario()
