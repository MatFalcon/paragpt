from odoo import api, fields, models, _, release


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    currency_rate = fields.Float(string='Tipo de Cambio')
    freeze_currency_rate = fields.Boolean(string='Congelar Tipo de Cambio', default=False)

    @api.onchange('currency_id', 'date')
    def get_tipo_cambio_default(self):
        # interfaces_tipo_cambio_compra_venta/models/account_payment.py
        if self.freeze_currency_rate: return
        currency_rate = 1
        if self.currency_id:
            _get_conversion_rate = self.currency_id._get_conversion_rate
            if self.payment_type in ['inbound', 'outbound']:
                if self.payment_type in ['inbound']:
                    _get_conversion_rate = self.currency_id._get_conversion_rate_tipo_cambio_comprador
                elif self.payment_type in ['outbound']:
                    _get_conversion_rate = self.currency_id._get_conversion_rate_tipo_cambio_vendedor
            currency_rate = _get_conversion_rate(
                self.currency_id,
                self.company_id.currency_id,
                self.company_id,
                (self.date or self.invoice_date or fields.date.today())
            )
        if self.currency_rate != currency_rate:
            self.currency_rate = currency_rate

    @api.onchange('date', 'currency_id', 'currency_rate')
    def _onchange_currency(self):
        # interfaces_tipo_cambio_compra_venta/models/account_payment.py
        self.get_tipo_cambio_default()

    @api.onchange('freeze_currency_rate')
    def _onchange_freeze_currency_rate(self):
        # interfaces_tipo_cambio_compra_venta/models/account_payment.py
        if not self.freeze_currency_rate:
            self._onchange_currency()

    if release.major_version in ['16.0']:
        def _prepare_move_line_default_vals(self, write_off_line_vals=None):
            # interfaces_tipo_cambio_compra_venta/models/account_payment.py
            ''' Prepare the dictionary to create the default account.move.lines for the current payment.
            :param write_off_line_vals: Optional list of dictionaries to create a write-off account.move.line easily containing:
                * amount:       The amount to be added to the counterpart amount.
                * name:         The label to set on the line.
                * account_id:   The account on which create the write-off.
            :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
            '''
            self.ensure_one()
            write_off_line_vals = write_off_line_vals or {}

            if not self.outstanding_account_id:
                raise UserError(_(
                    "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                    self.payment_method_line_id.name, self.journal_id.display_name))

            # Compute amounts.
            write_off_line_vals_list = write_off_line_vals or []
            write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
            write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -self.amount
            else:
                liquidity_amount_currency = 0.0

            parameters = {
                'to_currency': self.company_id.currency_id,
                'company': self.company_id,
                'date': self.date,
                'force_rate': self.currency_rate,
            }
            _convert = self.currency_id._convert_tipo_cambio_vendedor

            parameters.update({'from_amount': liquidity_amount_currency})
            liquidity_balance = _convert(**parameters)

            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance
            currency_id = self.currency_id.id

            # Compute a default label to set on the journal items.
            liquidity_line_name = ''.join(x[1] for x in self._get_liquidity_aml_display_name_list())
            counterpart_line_name = ''.join(x[1] for x in self._get_counterpart_aml_display_name_list())

            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                },
                # Receivable / Payable.
                {
                    'name': counterpart_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                },
            ]
            return line_vals_list + write_off_line_vals_list

    if release.major_version in ['15.0']:
        def _prepare_move_line_default_vals(self, write_off_line_vals=None):
            # interfaces_tipo_cambio_compra_venta/models/account_payment.py
            ''' Prepare the dictionary to create the default account.move.lines for the current payment.
            :param write_off_line_vals: Optional dictionary to create a write-off account.move.line easily containing:
                * amount:       The amount to be added to the counterpart amount.
                * name:         The label to set on the line.
                * account_id:   The account on which create the write-off.
            :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
            '''
            self.ensure_one()
            write_off_line_vals = write_off_line_vals or {}

            if not self.outstanding_account_id:
                raise UserError(_(
                    "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                    self.payment_method_line_id.name, self.journal_id.display_name))

            # Compute amounts.
            write_off_amount_currency = write_off_line_vals.get('amount', 0.0)

            if self.payment_type == 'inbound':
                # Receive money.
                liquidity_amount_currency = self.amount
            elif self.payment_type == 'outbound':
                # Send money.
                liquidity_amount_currency = -self.amount
                write_off_amount_currency *= -1
            else:
                liquidity_amount_currency = write_off_amount_currency = 0.0

            parameters = {
                'to_currency': self.company_id.currency_id,
                'company': self.company_id,
                'date': self.date,
                'force_rate': self.currency_rate,
            }
            _convert = self.currency_id._convert_tipo_cambio_vendedor

            parameters.update({'from_amount': write_off_amount_currency})
            write_off_balance = _convert(**parameters)
            parameters.update({'from_amount': liquidity_amount_currency})
            liquidity_balance = _convert(**parameters)
            counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
            counterpart_balance = -liquidity_balance - write_off_balance
            currency_id = self.currency_id.id

            if self.is_internal_transfer:
                if self.payment_type == 'inbound':
                    liquidity_line_name = _('Transfer to %s', self.journal_id.name)
                else:  # payment.payment_type == 'outbound':
                    liquidity_line_name = _('Transfer from %s', self.journal_id.name)
            else:
                liquidity_line_name = self.payment_reference

            # Compute a default label to set on the journal items.

            payment_display_name = self._prepare_payment_display_name()

            default_line_name = self.env['account.move.line']._get_default_line_name(
                _("Internal Transfer") if self.is_internal_transfer else payment_display_name['%s-%s' % (self.payment_type, self.partner_type)],
                self.amount,
                self.currency_id,
                self.date,
                partner=self.partner_id,
            )

            line_vals_list = [
                # Liquidity line.
                {
                    'name': liquidity_line_name or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': liquidity_amount_currency,
                    'currency_id': currency_id,
                    'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                    'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.outstanding_account_id.id,
                },
                # Receivable / Payable.
                {
                    'name': self.payment_reference or default_line_name,
                    'date_maturity': self.date,
                    'amount_currency': counterpart_amount_currency,
                    'currency_id': currency_id,
                    'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                    'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': self.destination_account_id.id,
                },
            ]
            if not self.currency_id.is_zero(write_off_amount_currency):
                # Write-off line.
                line_vals_list.append({
                    'name': write_off_line_vals.get('name') or default_line_name,
                    'amount_currency': write_off_amount_currency,
                    'currency_id': currency_id,
                    'debit': write_off_balance if write_off_balance > 0.0 else 0.0,
                    'credit': -write_off_balance if write_off_balance < 0.0 else 0.0,
                    'partner_id': self.partner_id.id,
                    'account_id': write_off_line_vals.get('account_id'),
                })
            return line_vals_list
