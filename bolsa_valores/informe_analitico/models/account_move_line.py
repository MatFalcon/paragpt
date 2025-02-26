from odoo import _, api, fields, models, exceptions


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def compute_secondary_values(self):
        res = super(AccountMoveLine,self).compute_secondary_values()
        if self.analytic_line_ids:
            for l in self.analytic_line_ids:
                l.write({'debit_ms': self.debit_ms,
                         'credit_ms': self.credit_ms,
                         'secondary_currency_id': self.secondary_currency_id.id,
                         'tipo_cambio': self.tipo_cambio,
                         'balance_ms': l.amount / self.tipo_cambio})
        return res