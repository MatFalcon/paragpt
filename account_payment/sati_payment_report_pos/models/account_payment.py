# -*- coding: utf-8 -*-
from odoo import models, fields, api

class AccountPayment(models.Model):
    _inherit = "account.payment"

    amount_currency = fields.Float(compute="_compute_amount_currency", string="Amount local currency")
    amount_local = fields.Float(compute="_compute_amount_currency", string="Amount foreign currency")
    totales = fields.Float(compute="_compute_amount_currency", string="Totals")
    # Se define como campo computado en lugar de un related, para evitar la referencia a un campo inexistente.
    cuenta_analitica = fields.Many2one(
        'account.analytic.account',
        string="Analytic Account",
        compute="_compute_cuenta_analitica",
        store=True
    )
    report_date = fields.Date(related='date', string='Fecha Reporte')

    @api.depends('reconciled_invoice_ids.line_ids')
    def _compute_cuenta_analitica(self):
        for rec in self:
            analytic_account = False
            for line in rec.reconciled_invoice_ids.mapped('line_ids'):
                if hasattr(line, 'analytic_account_id') and line.analytic_account_id:
                    analytic_account = line.analytic_account_id
                    break
            rec.cuenta_analitica = analytic_account

    @api.depends('amount', 'currency_id')
    def _compute_amount_currency(self):
        for payment in self:
            payment.amount_local = 0
            payment.amount_currency = 0
            if payment.currency_id != payment.company_id.currency_id:
                date_payment = payment.date
                currency_rate = self.env['res.currency.rate'].search(
                    [('currency_id', '=', payment.currency_id.id), ('name', '<=', date_payment)],
                    order='name desc', limit=1
                )
                if currency_rate:
                    if not payment.recibo_id.pagos_facturas_ids:
                        payment.amount_local = payment.amount * currency_rate.set_venta
                        payment.amount_currency = payment.amount
                    elif payment.recibo_id.pagos_facturas_ids:
                        for p in payment.recibo_id.pagos_facturas_ids:
                            payment.amount_local = p.monto * currency_rate.set_venta
                            payment.amount_currency = p.monto
            else:
                payment.amount_local = payment.amount
                payment.amount_currency = 0


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    amount_currency = fields.Float(compute="_compute_amount_currency", string="Amount local currency")
    amount_local = fields.Float(compute="_compute_amount_currency", string="Amount foreign currency")
    totales = fields.Float(compute="_compute_amount_currency", string="Totals")
    report_date = fields.Date(string='Fecha Reporte', compute='_compute_report_date', store=True)

    @api.depends('payment_date')
    def _compute_report_date(self):
        for record in self:
            if record.payment_date:
                record.report_date = record.payment_date.date()
            else:
                record.report_date = False

    @api.depends('amount', 'currency_id')
    def _compute_amount_currency(self):
        for pos in self:
            pos.amount_local = 0
            pos.amount_currency = 0
            if pos.currency_id != pos.company_id.currency_id:
                date_payment = pos.payment_date
                currency_rate = self.env['res.currency.rate'].search(
                    [('currency_id', '=', pos.currency_id.id), ('name', '<=', date_payment)],
                    order='name desc', limit=1
                )
                if currency_rate:
                    pos.amount_currency = pos.amount
            else:
                pos.amount_local = pos.amount
                pos.amount_currency = 0
