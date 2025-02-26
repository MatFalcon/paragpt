# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools
from . import amount_to_text_spanish


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # computed_daily_wage = fields.Float(string='Salario Diario', compute='get_computed_daily_wage')
    real_wage = fields.Float(string='Salario', compute='_get_real_wage')
    real_wage_string = fields.Char(string='Salario con formato', compute='_get_real_wage')
    real_wage_words = fields.Char(string='Salario en español', compute='_get_real_wage')
    daily_wage = fields.Monetary('Salario por Día')

    check_sueldo_minimo = fields.Boolean('Percibe Sueldo mínimo', default=False)
    check_jornal_minimo = fields.Boolean('Percibe Jornal mínimo', default=False)
    number_of_planned_work_days = fields.Integer(string='Días a trabajar')
    appears_in_mtess_reports = fields.Boolean('Aparece en los reportes para el MTESS', default=True)

    def get_computed_daily_wage(self, request_date):
        # reportes_ministerio_trabajo/models/hr_contract.py
        if self.wage_type == 'daily':
            salario = self.daily_wage if not self.check_jornal_minimo else (
                    self.env['wizard_salario_minimo'].get_salario_vigente(request_date) / 26
            )
        elif self.wage_type == 'hourly':
            salario = self.hourly_wage * 8
        else:
            salario = (
                          self.wage if not self.check_sueldo_minimo else self.env[
                              'wizard_salario_minimo'].get_salario_vigente(request_date)
                      ) / 30
        return salario

    def get_real_wage(self, request_date=fields.Date.today()):
        # reportes_ministerio_trabajo/models/hr_contract.py
        if self.wage_type == 'daily':
            salario = self.daily_wage if not self.check_jornal_minimo else (self.env['wizard_salario_minimo'].get_salario_vigente(request_date) / 26)
        elif self.wage_type == 'hourly':
            salario = self.hourly_wage * 8
        else:
            salario = (self.wage if not self.check_sueldo_minimo else self.env['wizard_salario_minimo'].get_salario_vigente(request_date))
        result = {
            'real_wage': salario,
            'real_wage_string': "{:,.0f}".format(salario).replace(',', '.'),
            'real_wage_words': amount_to_text_spanish.to_word(int(salario)),
        }
        return result

    def _get_real_wage(self, request_date=fields.Date.today()):
        # reportes_ministerio_trabajo/models/hr_contract.py
        result = self.get_real_wage(request_date)
        self.real_wage = result['real_wage']
        self.real_wage_string = result['real_wage_string']
        self.real_wage_words = result['real_wage_words']

        return result

    def create_contract_active_history(self):
        # reportes_ministerio_trabajo/models/hr_contract.py
        for this in self:
            histories = self.env['hr.contract.active_history'].search([('contract_id', '=', this.id)])
            data = {
                'contract_id': this.id,
                'state': this.state,
                'date_start': this.date_start,
                'date_end': this.date_end,
                'wage': this.get_real_wage(tools.date.today()).get('real_wage'),
                'wage_type': this.wage_type
            }
            if histories:
                histories.write(data)
            else:
                histories.create(data)

    @api.model
    def create(self, vals):
        # reportes_ministerio_trabajo/models/hr_contract.py
        r = super(HrContract, self).create(vals)
        r.create_contract_active_history()
        return r

    def write(self, vals):
        # reportes_ministerio_trabajo/models/hr_contract.py
        r = super(HrContract, self).write(vals)
        self.create_contract_active_history()
        return r
