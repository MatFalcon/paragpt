from odoo import _, api, fields, models, exceptions
from odoo.osv import expression
from collections import defaultdict
from datetime import timedelta


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    secondary_currency_id = fields.Many2one(
        "res.currency", string="Moneda secundaria", store=True)
    tipo_cambio = fields.Float(string="Cotización")
    debit_ms = fields.Monetary(
        string="Débito (MS)", currency_field="secondary_currency_id", store=True)
    credit_ms = fields.Monetary(
        string="Crédito (MS)", currency_field="secondary_currency_id", store=True)
    balance_ms = fields.Monetary(
        string="Importe (MS)", currency_field="secondary_currency_id", compute="_compute_debit_credit_balance_ms")

    @api.depends('line_ids.balance_ms')
    def _compute_debit_credit_balance_ms(self):
        Curr = self.env.company.secondary_currency_id
        if Curr:
            analytic_line_obj = self.env['account.analytic.line']
            domain = [
                ('account_id', 'in', self.ids),
                ('company_id', 'in', [False] + self.env.companies.ids)
            ]
            if self._context.get('from_date', False):
                domain.append(('date', '>=', self._context['from_date']))
            if self._context.get('to_date', False):
                domain.append(('date', '<=', self._context['to_date']))
            if self._context.get('tag_ids'):
                tag_domain = expression.OR([[('tag_ids', 'in', [tag])] for tag in self._context['tag_ids']])
                domain = expression.AND([domain, tag_domain])

            user_currency = self.env.company.secondary_currency_id
            credit_groups = analytic_line_obj.read_group(
                domain=domain + [('amount', '>=', 0.0)],
                fields=['account_id', 'secondary_currency_id', 'balance_ms'],
                groupby=['account_id', 'secondary_currency_id'],
                lazy=False,
            )
            data_credit = defaultdict(float)
            for l in credit_groups:
                if l['balance_ms']:
                    data_credit[l['account_id'][0]] += Curr.browse(l['secondary_currency_id'][0])._convert(
                        l['balance_ms'], user_currency, self.env.company, fields.Date.today())

            debit_groups = analytic_line_obj.read_group(
                domain=domain + [('amount', '<', 0.0)],
                fields=['account_id', 'secondary_currency_id', 'balance_ms'],
                groupby=['account_id', 'secondary_currency_id'],
                lazy=False,
            )
            data_debit = defaultdict(float)
            for l in debit_groups:
                if l['balance_ms']:
                    data_debit[l['account_id'][0]] += Curr.browse(l['secondary_currency_id'][0])._convert(
                        l['balance_ms'], user_currency, self.env.company, fields.Date.today())

            for account in self:
                account.debit_ms = abs(data_debit.get(account.id, 0.0))
                account.credit_ms = data_credit.get(account.id, 0.0)
                account.balance_ms = account.credit_ms - account.debit_ms
                account.secondary_currency_id = self.env.company.secondary_currency_id.id


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    secondary_currency_id = fields.Many2one(
        "res.currency", string="Moneda secundaria")
    tipo_cambio = fields.Float(string="Cotización")
    debit_ms = fields.Monetary(
        string="Débito (MS)", currency_field="secondary_currency_id")
    credit_ms = fields.Monetary(
        string="Crédito (MS)", currency_field="secondary_currency_id")
    balance_ms = fields.Monetary(
        string="Importe (MS)", currency_field="secondary_currency_id")