from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move.line'

    orden_pago_factura = fields.One2many('account.orden.pago.factura','move_line_id',string="Líneas de op")
    op_id = fields.Many2one(related="orden_pago_factura.orden_pago_id",store=True)

    def _compute_amount_fields(self, amount, src_currency, company_currency):
        """ Helper function to compute value for fields debit/credit/amount_currency based on an amount and the currencies given in parameter"""
        amount_currency = False
        currency_id = False
        date = self.env.context.get('date') or fields.Date.today()
        company = self.env.context.get('company_id')
        company = self.env['res.company'].browse(company) if company else self.env.company
        if src_currency and src_currency != company_currency:
            amount_currency = amount
            amount = src_currency._convert(amount, company_currency, company, date)
            currency_id = src_currency.id
        debit = amount > 0 and amount or 0.0
        credit = amount < 0 and -amount or 0.0
        return debit, credit, amount_currency, currency_id