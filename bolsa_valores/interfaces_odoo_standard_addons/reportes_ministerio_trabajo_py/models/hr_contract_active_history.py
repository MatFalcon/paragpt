# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class HrContractActiveHistory(models.Model):
    _name = 'hr.contract.active_history'
    _description = 'Historial de contratos de los empleados'

    contract_id = fields.Many2one('hr.contract')
    state = fields.Selection(selection=[('draft', 'draft'), ('open', 'open'), ('close', 'close'), ('cancel', 'cancel')])
    date_start = fields.Date()
    date_end = fields.Date()
    wage = fields.Float()
    wage_type = fields.Selection(selection=[('monthly', 'monthly'), ('daily', 'daily'), ('hourly', 'hourly')])

    @api.model
    def get_contracts(self, company_ids, date_from, date_to):
        # reportes_ministerio_trabajo/models/hr_contract_active_history.py
        domain = [
            ('contract_id', '!=', False),
            ('contract_id.employee_id', '!=', False),
            ('contract_id.company_id', 'in', company_ids.ids),
            ('date_start', '<=', date_to),
            '|',
            ('date_end', '>=', date_from),
            ('date_end', '=', False)]
        return self.search(domain).mapped('contract_id')
