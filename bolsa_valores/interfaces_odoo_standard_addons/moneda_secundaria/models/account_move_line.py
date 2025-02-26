from odoo import _, api, fields, models, exceptions

from datetime import timedelta


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        res = super(AccountMove, self)._post(soft)
        for move in self:
            for line in move.line_ids:
                line.compute_secondary_values()
        return res


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    secondary_currency_id = fields.Many2one(
        "res.currency", string="Moneda secundaria")
    tipo_cambio = fields.Float(string="Cotización")
    debit_ms = fields.Monetary(
        string="Débito (MS)", currency_field="secondary_currency_id")
    credit_ms = fields.Monetary(
        string="Crédito (MS)", currency_field="secondary_currency_id")
    balance_ms = fields.Monetary(
        string="Saldo (MS)", currency_field="secondary_currency_id")

    def compute_secondary_values(self):
        secondary_currency_id = self.env.company.secondary_currency_id
        # today=fields.Date.today()
        # rates=secondary_currency_id.rate_ids.filtered(lambda x:x.name==(today-timedelta(days=1)) or x.name==today)
        # if not rates:
        #     raise exceptions.ValidationError("Debe cargar una cotización para la moneda %s con fecha de ayer u hoy"%secondary_currency_id.name)
        if secondary_currency_id == self.currency_id:
            tipo_cambio = 1
            if self.balance and self.amount_currency:
                tipo_cambio = abs(self.balance) / abs(self.amount_currency)
        else:
            # tipo_cambio = secondary_currency_id.inverse_rate
            tipo_cambio = secondary_currency_id.rate_ids.filtered(lambda x: x.name <= self.date)
            if tipo_cambio: tipo_cambio = tipo_cambio[0].inverse_company_rate
            if not tipo_cambio:
                raise exceptions.ValidationError('No existe un tipo de cambio definido para la fecha')
        debit_ms = self.debit / tipo_cambio
        credit_ms = self.credit / tipo_cambio
        balance_ms = self.balance / tipo_cambio
        self.write({'debit_ms': debit_ms,
                    'credit_ms': credit_ms,
                    'secondary_currency_id': secondary_currency_id,
                    'tipo_cambio': tipo_cambio,
                    'balance_ms': balance_ms})
