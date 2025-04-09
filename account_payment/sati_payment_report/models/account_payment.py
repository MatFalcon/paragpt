from odoo import models, fields, api


class AccountPayment(models.Model):
    _inherit = "account.payment"

    amount_currency = fields.Float(compute="_compute_amount_currency", string="Amount local currency")
    amount_local = fields.Float(compute="_compute_amount_currency", string="Amount foreign currency")
    totales = fields.Float(compute="_compute_amount_currency", string="Totals")


    @api.depends('amount', 'currency_id')
    def _compute_amount_currency(self):
        for payment in self:
            payment.amount_local = 0
            payment.amount_currency = 0
            if payment.currency_id != payment.company_id.currency_id:
                # The payment is in a foreign currency
                date_payment = payment.date
                currency_rate = self.env['res.currency.rate'].search(
                    [('currency_id', '=', payment.currency_id.id), ('name', '<=', date_payment)],
                    order='name desc', limit=1)
                if currency_rate:
                    if not payment.recibo_id.pagos_facturas_ids:
                        payment.amount_local = payment.amount * currency_rate.set_venta
                        payment.amount_currency = payment.amount
                    elif payment.recibo_id.pagos_facturas_ids:
                        for p in payment.recibo_id.pagos_facturas_ids:
                            payment.amount_local = p.monto * currency_rate.set_venta
                            payment.amount_currency = p.monto

            else:
                # The payment is in the company's currency

                payment.amount_local = payment.amount
                payment.amount_currency = 0
