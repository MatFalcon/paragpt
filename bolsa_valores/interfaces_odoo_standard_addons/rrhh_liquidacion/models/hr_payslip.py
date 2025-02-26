# -*- coding: utf-8 -*-
import pytz
from odoo import models, fields, api, exceptions, _


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    es_liquidacion = fields.Boolean(default=False)
    liquidacion_dias_tabajados = fields.Char()
    liquidacion_antiguedad = fields.Char()
    liquidacion_fecha_inicio = fields.Date()
    liquidacion_fecha_fin = fields.Date()
    liquidacion_motivo = fields.Char()
    liquidacion_dias_indemnizacion = fields.Integer()
    liquidacion_preaviso_sin_comunicar = fields.Integer()
    liquidacion_dias_vacaciones_causadas = fields.Integer()
    liquidacion_dias_vacaciones_proporcionales = fields.Integer()
    liquidacion_dias_vacaciones_acumuladas = fields.Integer()
    liquidacion_periodo_prueba = fields.Boolean()
    testigo_id = fields.Many2one('hr.employee', string='Testitgo')

    def get_novedades(self):
        # rrhh_liquidacion/models/hr_payslip.py
        if self.structure_type_tag not in ['liquidacion']:
            return super(HrPayslip, self).get_novedades()
        else:
            return self.env['hr.novedades'].search([
                ('employee_id', '=', self.employee_id.id),
                ('contract_id', '=', self.contract_id.id),
                '|',
                ('state', '=', 'done'),
                ('payslip_id', '=', self.id),
            ])
