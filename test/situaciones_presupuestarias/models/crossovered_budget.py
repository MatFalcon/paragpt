from odoo import _, api, fields, models, exceptions
from odoo.osv import expression
from collections import defaultdict
from datetime import date, datetime, timedelta


class AccountPaymentRegister(models.TransientModel):
    _name = 'crossovered.budget.register'
    _description = 'Registro de Lineas de Situacion presupuestaria'

    user_type_id = fields.Many2one('account.account.type', string="Tipo de cuenta")
    general_budget_ids = fields.Many2many('account.budget.post', string="Situaciones presupuestarias")
    periodo = fields.Selection([
        ('mensual', 'Mensual'),
        ('anual', 'Anual')
    ], string="Periodo", default="mensual", required=True)
    analytic_account_ids = fields.Many2many('account.analytic.account', string="Cuentas analiticas")

    def get_first_date_of_month(self, year, month):
        first_date = datetime(year, month, 1)
        return first_date.strftime("%Y-%m-%d")

    def get_last_date_of_month(self, year, month):
        if month == 12:
            last_date = datetime(year, month, 31)
        else:
            last_date = datetime(year, month + 1, 1) + timedelta(days=-1)
        return last_date.strftime("%Y-%m-%d")

    @api.onchange('user_type_id')
    @api.depends('user_type_id')
    def onchangeUserType(self):
        if self.user_type_id:
            crossovered_lines_ids = self.env['account.budget.post'].search([('account_ids.user_type_id','=',self.user_type_id.id)])
            if crossovered_lines_ids:
                self.write({'general_budget_ids': [(6,0,crossovered_lines_ids.ids)]})
            else:
                self.write({'general_budget_ids':[(5,0,0)]})
        #print(self._context.get('active_id'))

    def add_lines_dates(self, date_from, date_to):
        line_ids = []
        crossovered_budget = self.env['crossovered.budget'].browse(self._context.get('active_id'))
        if self.analytic_account_ids:
            for i in self.analytic_account_ids:
                for x in self.general_budget_ids:
                    line_ids.append((0, 0, {
                        'general_budget_id': x.id,
                        'date_from': date_from,
                        'date_to': date_to,
                        'analytic_account_id': i.id,
                        'planned_amount': 0
                    }))
        else:
            for x in self.general_budget_ids:
                line_ids.append((0, 0, {
                    'general_budget_id': x.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'planned_amount': 0
                }))
        crossovered_budget.write({'crossovered_budget_line':line_ids})


    def action_create_lines(self):
        crossovered_budget = self.env['crossovered.budget'].browse(self._context.get('active_id'))
        if not crossovered_budget:
            raise exceptions.ValidationError(
                'No existe un presupuesto.')
        if not self.general_budget_ids:
            raise exceptions.ValidationError(
                'No existen situaciones presupuestarias para agregar.')
        if self.periodo == 'anual':
            self.add_lines_dates(crossovered_budget.date_from, crossovered_budget.date_to)
        elif self.periodo == 'mensual':
            year_inicio = crossovered_budget.date_from.year
            year_fin = crossovered_budget.date_to.year
            if year_inicio == year_fin:
                mes_inicio = crossovered_budget.date_from.month
                mes_fin = crossovered_budget.date_to.month
                while mes_inicio <= mes_fin:
                    primer_dia = self.get_first_date_of_month(year_inicio,mes_inicio)
                    ultimo_dia = self.get_last_date_of_month(year_inicio,mes_inicio)
                    self.add_lines_dates(primer_dia, ultimo_dia)
                    mes_inicio = mes_inicio + 1
            elif year_inicio < year_fin:
                while year_inicio < year_fin:
                    ultimo_mes = 12
                    mes_inicio = crossovered_budget.date_from.month
                    while mes_inicio <= ultimo_mes:
                        primer_dia = self.get_first_date_of_month(year_inicio,mes_inicio)
                        ultimo_dia = self.get_last_date_of_month(year_inicio,mes_inicio)
                        self.add_lines_dates(primer_dia, ultimo_dia)
                        mes_inicio = mes_inicio + 1
                    year_inicio = year_inicio + 1
                if year_inicio == year_fin:
                    mes_inicio = 1
                    mes_fin = crossovered_budget.date_to.month
                    while mes_inicio <= mes_fin:
                        primer_dia = self.get_first_date_of_month(year_inicio, mes_inicio)
                        ultimo_dia = self.get_last_date_of_month(year_inicio, mes_inicio)
                        self.add_lines_dates(primer_dia, ultimo_dia)
                        mes_inicio = mes_inicio + 1

        return


class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'

    def button_agregar_lineas(self):
        return {
            'name': _('Agregar Lineas de Presupuesto'),
            'res_model': 'crossovered.budget.register',
            'view_mode': 'form',
            'context': {
                'active_id': self.id,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class CrossoveredBudgetLines(models.Model):
    _inherit = 'crossovered.budget.lines'

    difference_amount = fields.Float(string="Variación en importe", compute="difference_in_amount")

    def difference_in_amount(self):
        for i in self:
            i.difference_amount = i.planned_amount - i.practical_amount