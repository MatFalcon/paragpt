from odoo import fields, models, api, release


class AccountBankStatementLine(models.Model):
    _inherit = 'account.bank.statement.line'

    compute_currency_rate_for_line = fields.Boolean(default=False)
    currency_rate = fields.Float(string='Tipo de Cambio')
    freeze_currency_rate = fields.Boolean(string='Congelar Tipo de Cambio', default=False)

    @api.onchange('payment_ref', 'date')
    def get_tipo_cambio_default(self):
        # interfaces_tipo_cambio_compra_venta/models/account_bank_statement_line.py
        if self.freeze_currency_rate or not self.compute_currency_rate_for_line: return
        currency_rate = 1
        if self.currency_id:
            _get_conversion_rate = self.currency_id._get_conversion_rate
            currency_rate = _get_conversion_rate(
                self.currency_id,
                self.company_id.currency_id,
                self.company_id,
                (self.date or fields.date.today())
            )
        if self.currency_rate != currency_rate:
            self.currency_rate = currency_rate

    if release.major_version in ['16.0']:

        @api.onchange('date', 'currency_id', 'currency_rate')
        def _onchange_currency(self):
            # interfaces_tipo_cambio_compra_venta/models/account_bank_statement_line.py
            self.get_tipo_cambio_default()

        @api.onchange('freeze_currency_rate')
        def _onchange_freeze_currency_rate(self):
            # interfaces_tipo_cambio_compra_venta/models/account_bank_statement_line.py
            if not self.freeze_currency_rate:
                self._onchange_currency()

        def compute_currency_rate_for_move(self):
            for this in self:
                if this.compute_currency_rate_for_line and this.move_id and this.move_id.move_type == 'entry' and this.move_id.state == 'posted':
                    this.move_id.button_draft()
                    this.move_id.write({
                        'currency_rate': this.currency_rate,
                        'freeze_currency_rate': True,
                    })
                    this.move_id.with_context(check_move_validity=False)._onchange_currency()
                    this.move_id.line_ids._compute_currency_rate()
                    this.move_id.action_post()

        @api.model_create_multi
        def create(self, vals_list):
            # interfaces_tipo_cambio_compra_venta/models/account_bank_statement_line.py
            result = super().create(vals_list)
            result.compute_currency_rate_for_move()
            return result

        def write(self, vals):
            # interfaces_tipo_cambio_compra_venta/models/account_bank_statement_line.py
            result = super().write(vals)
            if any([field in vals for field in ['date', 'currency_id', 'currency_rate', 'amount']]):
                self.compute_currency_rate_for_move()
            return result
