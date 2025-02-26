# -*- coding: utf-8 -*-
import datetime
from odoo import models, fields, api


class HistorialSalario(models.Model):
    _name = 'historial.salario'
    _description = 'Historial de salarios cobrados'

    state = fields.Selection(string="Estado", selection=[('good', 'Confirmado'), ('bad', 'Cancelado')])
    real_wage = fields.Float(string='Salario Neto')
    bruto_para_aguinaldo = fields.Float(string='Monto bruto para aguinaldos')
    date_from = fields.Date('Fecha inicio')
    date_to = fields.Date('Fecha fin')
    payslip_id = fields.Many2one('hr.payslip', string='Nómina', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', related='payslip_id.employee_id')
    contract_id = fields.Many2one('hr.contract', related='payslip_id.contract_id')

    def get_salario_mes(self, employee_id=False, contract_id=False, anho=False, mes=False):
        # reportes_ministerio_trabajo/models/historial_salario.py
        if not employee_id or not contract_id or not mes or type(mes) != int or mes > 12 or not anho or type(anho) != int:
            return False
        else:
            historiales = self.search([('state', '=', 'good')]).filtered(
                lambda x: x.contract_id == contract_id and x.date_to.year == anho and x.date_to.month == mes
            )
            return sum([x.real_wage for x in historiales])
