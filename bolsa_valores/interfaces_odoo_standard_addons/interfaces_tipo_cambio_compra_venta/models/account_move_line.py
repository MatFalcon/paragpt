from odoo import api, fields, models, release


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    if release.major_version in ['16.0']:

        @api.depends('currency_id', 'company_id', 'move_id.date')
        def _compute_currency_rate(self):
            # interfaces_tipo_cambio_compra_venta/models/account_move_line.py
            result = super(AccountMoveLine, self)._compute_currency_rate()
            for line in self:
                if line.move_id.currency_rate:
                    old_quanity = line.quantity
                    line.currency_rate = 1 / line.move_id.currency_rate
                    line.quantity = old_quanity
            return result

        @api.model
        def _prepare_reconciliation_single_partial(self, debit_vals, credit_vals):
            # interfaces_tipo_cambio_compra_venta/models/account_move_line.py
            """ Prepare the values to create an account.partial.reconcile later when reconciling the dictionaries passed
            as parameters, each one representing an account.move.line.
            :param debit_vals:  The values of account.move.line to consider for a debit line.
            :param credit_vals: The values of account.move.line to consider for a credit line.
            :return:            A dictionary:
                * debit_vals:   None if the line has nothing left to reconcile.
                * credit_vals:  None if the line has nothing left to reconcile.
                * partial_vals: The newly computed values for the partial.
            """

            def is_payment(vals):
                return vals.get('is_payment') or (
                        vals.get('record')
                        and bool(vals['record'].move_id.payment_id or vals['record'].move_id.statement_line_id)
                )

            def get_odoo_rate(vals, other_line=None, self=None):
                if vals.get('record') and vals['record'].move_id.is_invoice(include_receipts=True):
                    exchange_rate_date = vals['record'].move_id.invoice_date
                else:
                    exchange_rate_date = vals['date']
                if not is_payment(vals) and other_line and is_payment(other_line):
                    exchange_rate_date = other_line['date']
                if self \
                        and self.env \
                        and self.env.context.get('active_model') \
                        and self.env.context.get('active_model') == 'account.move' \
                        and len(self.env.context.get('active_ids')) == 1:
                    return 1 / self.env[self.env.context.get('active_model')].browse(self.env.context.get('active_ids')).currency_rate
                return recon_currency._get_conversion_rate(company_currency, recon_currency, vals['company'], exchange_rate_date)

            def get_accounting_rate(vals):
                if company_currency.is_zero(vals['balance']) or vals['currency'].is_zero(vals['amount_currency']):
                    return None
                else:
                    return abs(vals['amount_currency']) / abs(vals['balance'])

            # ==== Determine the currency in which the reconciliation will be done ====
            # In this part, we retrieve the residual amounts, check if they are zero or not and determine in which
            # currency and at which rate the reconciliation will be done.

            res = {
                'debit_vals': debit_vals,
                'credit_vals': credit_vals,
            }
            remaining_debit_amount_curr = debit_vals['amount_residual_currency']
            remaining_credit_amount_curr = credit_vals['amount_residual_currency']
            remaining_debit_amount = debit_vals['amount_residual']
            remaining_credit_amount = credit_vals['amount_residual']

            company_currency = debit_vals['company'].currency_id
            has_debit_zero_residual = company_currency.is_zero(remaining_debit_amount)
            has_credit_zero_residual = company_currency.is_zero(remaining_credit_amount)
            has_debit_zero_residual_currency = debit_vals['currency'].is_zero(remaining_debit_amount_curr)
            has_credit_zero_residual_currency = credit_vals['currency'].is_zero(remaining_credit_amount_curr)
            is_rec_pay_account = debit_vals.get('record') \
                                 and debit_vals['record'].account_type in ('asset_receivable', 'liability_payable')

            if debit_vals['currency'] == credit_vals['currency'] == company_currency \
                    and not has_debit_zero_residual \
                    and not has_credit_zero_residual:
                # Everything is expressed in company's currency and there is something left to reconcile.
                recon_currency = company_currency
                debit_rate = credit_rate = 1.0
                recon_debit_amount = remaining_debit_amount
                recon_credit_amount = -remaining_credit_amount
            elif debit_vals['currency'] == company_currency \
                    and is_rec_pay_account \
                    and not has_debit_zero_residual \
                    and credit_vals['currency'] != company_currency \
                    and not has_credit_zero_residual_currency:
                # The credit line is using a foreign currency but not the opposite line.
                # In that case, convert the amount in company currency to the foreign currency one.
                recon_currency = credit_vals['currency']
                debit_rate = get_odoo_rate(debit_vals, other_line=credit_vals, self=self)
                credit_rate = get_accounting_rate(credit_vals)
                recon_debit_amount = recon_currency.round(remaining_debit_amount * debit_rate)
                recon_credit_amount = -remaining_credit_amount_curr

                # If there is nothing left after applying the rate to reconcile in foreign currency,
                # try to fallback on the company currency instead.
                if recon_currency.is_zero(recon_debit_amount) or recon_currency.is_zero(recon_credit_amount):
                    recon_currency = company_currency
                    debit_rate = 1
                    recon_debit_amount = remaining_debit_amount
                    recon_credit_amount = -remaining_credit_amount

            elif debit_vals['currency'] != company_currency \
                    and is_rec_pay_account \
                    and not has_debit_zero_residual_currency \
                    and credit_vals['currency'] == company_currency \
                    and not has_credit_zero_residual:
                # The debit line is using a foreign currency but not the opposite line.
                # In that case, convert the amount in company currency to the foreign currency one.
                recon_currency = debit_vals['currency']
                debit_rate = get_accounting_rate(debit_vals)
                credit_rate = get_odoo_rate(credit_vals, other_line=debit_vals)
                recon_debit_amount = remaining_debit_amount_curr
                recon_credit_amount = recon_currency.round(-remaining_credit_amount * credit_rate)

                # If there is nothing left after applying the rate to reconcile in foreign currency,
                # try to fallback on the company currency instead.
                if recon_currency.is_zero(recon_debit_amount) or recon_currency.is_zero(recon_credit_amount):
                    recon_currency = company_currency
                    credit_rate = 1
                    recon_debit_amount = remaining_debit_amount
                    recon_credit_amount = -remaining_credit_amount

            elif debit_vals['currency'] == credit_vals['currency'] \
                    and debit_vals['currency'] != company_currency \
                    and not has_debit_zero_residual_currency \
                    and not has_credit_zero_residual_currency:
                # Both lines are sharing the same foreign currency.
                recon_currency = debit_vals['currency']
                debit_rate = get_accounting_rate(debit_vals)
                credit_rate = get_accounting_rate(credit_vals)
                recon_debit_amount = remaining_debit_amount_curr
                recon_credit_amount = -remaining_credit_amount_curr
            elif debit_vals['currency'] == credit_vals['currency'] \
                    and debit_vals['currency'] != company_currency \
                    and (has_debit_zero_residual_currency or has_credit_zero_residual_currency):
                # Special case for exchange difference lines. In that case, both lines are sharing the same foreign
                # currency but at least one has no amount in foreign currency.
                # In that case, we don't want a rate for the opposite line because the exchange difference is supposed
                # to reduce only the amount in company currency but not the foreign one.
                recon_currency = company_currency
                debit_rate = None
                credit_rate = None
                recon_debit_amount = remaining_debit_amount
                recon_credit_amount = -remaining_credit_amount
            else:
                # Multiple involved foreign currencies. The reconciliation is done using the currency of the company.
                recon_currency = company_currency
                debit_rate = get_accounting_rate(debit_vals)
                credit_rate = get_accounting_rate(credit_vals)
                recon_debit_amount = remaining_debit_amount
                recon_credit_amount = -remaining_credit_amount

            # Check if there is something left to reconcile. Move to the next loop iteration if not.
            skip_reconciliation = False
            if recon_currency.is_zero(recon_debit_amount):
                res['debit_vals'] = None
                skip_reconciliation = True
            if recon_currency.is_zero(recon_credit_amount):
                res['credit_vals'] = None
                skip_reconciliation = True
            if skip_reconciliation:
                return res

            # ==== Match both lines together and compute amounts to reconcile ====

            # Determine which line is fully matched by the other.
            compare_amounts = recon_currency.compare_amounts(recon_debit_amount, recon_credit_amount)
            min_recon_amount = min(recon_debit_amount, recon_credit_amount)
            debit_fully_matched = compare_amounts <= 0
            credit_fully_matched = compare_amounts >= 0

            # ==== Computation of partial amounts ====
            if recon_currency == company_currency:
                # Compute the partial amount expressed in company currency.
                partial_amount = min_recon_amount

                # Compute the partial amount expressed in foreign currency.
                if debit_rate:
                    partial_debit_amount_currency = debit_vals['currency'].round(debit_rate * min_recon_amount)
                    partial_debit_amount_currency = min(partial_debit_amount_currency, remaining_debit_amount_curr)
                else:
                    partial_debit_amount_currency = 0.0
                if credit_rate:
                    partial_credit_amount_currency = credit_vals['currency'].round(credit_rate * min_recon_amount)
                    partial_credit_amount_currency = min(partial_credit_amount_currency, -remaining_credit_amount_curr)
                else:
                    partial_credit_amount_currency = 0.0

            else:
                # recon_currency != company_currency
                # Compute the partial amount expressed in company currency.
                if debit_rate:
                    partial_debit_amount = company_currency.round(min_recon_amount / debit_rate)
                    partial_debit_amount = min(partial_debit_amount, remaining_debit_amount)
                else:
                    partial_debit_amount = 0.0
                if credit_rate:
                    partial_credit_amount = company_currency.round(min_recon_amount / credit_rate)
                    partial_credit_amount = min(partial_credit_amount, -remaining_credit_amount)
                else:
                    partial_credit_amount = 0.0
                partial_amount = min(partial_debit_amount, partial_credit_amount)

                # Compute the partial amount expressed in foreign currency.
                # Take care to handle the case when a line expressed in company currency is mimicking the foreign
                # currency of the opposite line.
                if debit_vals['currency'] == company_currency:
                    partial_debit_amount_currency = partial_amount
                else:
                    partial_debit_amount_currency = min_recon_amount
                if credit_vals['currency'] == company_currency:
                    partial_credit_amount_currency = partial_amount
                else:
                    partial_credit_amount_currency = min_recon_amount

            # Computation of the partial exchange difference. You can skip this part using the
            # `no_exchange_difference` context key (when reconciling an exchange difference for example).
            if not self._context.get('no_exchange_difference'):
                exchange_lines_to_fix = self.env['account.move.line']
                amounts_list = []
                if recon_currency == company_currency:
                    if debit_fully_matched:
                        debit_exchange_amount = remaining_debit_amount_curr - partial_debit_amount_currency
                        if not debit_vals['currency'].is_zero(debit_exchange_amount):
                            if debit_vals.get('record'):
                                exchange_lines_to_fix += debit_vals['record']
                            amounts_list.append({'amount_residual_currency': debit_exchange_amount})
                            remaining_debit_amount_curr -= debit_exchange_amount
                    if credit_fully_matched:
                        credit_exchange_amount = remaining_credit_amount_curr + partial_credit_amount_currency
                        if not credit_vals['currency'].is_zero(credit_exchange_amount):
                            if credit_vals.get('record'):
                                exchange_lines_to_fix += credit_vals['record']
                            amounts_list.append({'amount_residual_currency': credit_exchange_amount})
                            remaining_credit_amount_curr += credit_exchange_amount

                else:
                    if debit_fully_matched:
                        # Create an exchange difference on the remaining amount expressed in company's currency.
                        debit_exchange_amount = remaining_debit_amount - partial_amount
                        if not company_currency.is_zero(debit_exchange_amount):
                            if debit_vals.get('record'):
                                exchange_lines_to_fix += debit_vals['record']
                            amounts_list.append({'amount_residual': debit_exchange_amount})
                            remaining_debit_amount -= debit_exchange_amount
                            if debit_vals['currency'] == company_currency:
                                remaining_debit_amount_curr -= debit_exchange_amount
                    else:
                        # Create an exchange difference ensuring the rate between the residual amounts expressed in
                        # both foreign and company's currency is still consistent regarding the rate between
                        # 'amount_currency' & 'balance'.
                        debit_exchange_amount = partial_debit_amount - partial_amount
                        if company_currency.compare_amounts(debit_exchange_amount, 0.0) > 0:
                            if debit_vals.get('record'):
                                exchange_lines_to_fix += debit_vals['record']
                            amounts_list.append({'amount_residual': debit_exchange_amount})
                            remaining_debit_amount -= debit_exchange_amount
                            if debit_vals['currency'] == company_currency:
                                remaining_debit_amount_curr -= debit_exchange_amount

                    if credit_fully_matched:
                        # Create an exchange difference on the remaining amount expressed in company's currency.
                        credit_exchange_amount = remaining_credit_amount + partial_amount
                        if not company_currency.is_zero(credit_exchange_amount):
                            if credit_vals.get('record'):
                                exchange_lines_to_fix += credit_vals['record']
                            amounts_list.append({'amount_residual': credit_exchange_amount})
                            remaining_credit_amount -= credit_exchange_amount
                            if credit_vals['currency'] == company_currency:
                                remaining_credit_amount_curr -= credit_exchange_amount
                    else:
                        # Create an exchange difference ensuring the rate between the residual amounts expressed in
                        # both foreign and company's currency is still consistent regarding the rate between
                        # 'amount_currency' & 'balance'.
                        credit_exchange_amount = partial_amount - partial_credit_amount
                        if company_currency.compare_amounts(credit_exchange_amount, 0.0) < 0:
                            if credit_vals.get('record'):
                                exchange_lines_to_fix += credit_vals['record']
                            amounts_list.append({'amount_residual': credit_exchange_amount})
                            remaining_credit_amount -= credit_exchange_amount
                            if credit_vals['currency'] == company_currency:
                                remaining_credit_amount_curr -= credit_exchange_amount

                if exchange_lines_to_fix:
                    res['exchange_vals'] = exchange_lines_to_fix._prepare_exchange_difference_move_vals(
                        amounts_list,
                        exchange_date=max(debit_vals['date'], credit_vals['date']),
                    )

            # ==== Create partials ====

            remaining_debit_amount -= partial_amount
            remaining_credit_amount += partial_amount
            remaining_debit_amount_curr -= partial_debit_amount_currency
            remaining_credit_amount_curr += partial_credit_amount_currency

            res['partial_vals'] = {
                'amount': partial_amount,
                'debit_amount_currency': partial_debit_amount_currency,
                'credit_amount_currency': partial_credit_amount_currency,
                'debit_move_id': debit_vals.get('record') and debit_vals['record'].id,
                'credit_move_id': credit_vals.get('record') and credit_vals['record'].id,
            }

            debit_vals['amount_residual'] = remaining_debit_amount
            debit_vals['amount_residual_currency'] = remaining_debit_amount_curr
            credit_vals['amount_residual'] = remaining_credit_amount
            credit_vals['amount_residual_currency'] = remaining_credit_amount_curr

            if debit_fully_matched:
                res['debit_vals'] = None
            if credit_fully_matched:
                res['credit_vals'] = None
            return res

    if release.major_version in ['15.0']:
        @api.model
        def _get_fields_onchange_subtotal_model(self, price_subtotal, move_type, currency, company, date):
            # interfaces_tipo_cambio_compra_venta/models/account_move_line.py
            ''' This method is used to recompute the values of 'amount_currency', 'debit', 'credit' due to a change made
            in some business fields (affecting the 'price_subtotal' field).

            :param price_subtotal:  The untaxed amount.
            :param move_type:       The type of the move.
            :param currency:        The line's currency.
            :param company:         The move's company.
            :param date:            The move's date.
            :return:                A dictionary containing 'debit', 'credit', 'amount_currency'.
            '''
            result = super(AccountMoveLine, self)._get_fields_onchange_subtotal_model(price_subtotal, move_type, currency, company, date)
            parameters = {
                'from_amount': result.get('amount_currency'),
                'to_currency': company.currency_id,
                'company': company,
                'date': date or fields.Date.context_today(self),
            }
            _convert = currency._convert
            if move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']:
                parameters.update({'force_rate': self.move_id.currency_rate})
                if move_type in ['out_invoice', 'out_refund']:
                    _convert = currency._convert_tipo_cambio_comprador
                if move_type in ['in_invoice', 'in_refund']:
                    _convert = currency._convert_tipo_cambio_vendedor

            balance = _convert(**parameters)
            result.update({
                'debit': balance > 0.0 and balance or 0.0,
                'credit': balance < 0.0 and -balance or 0.0,
            })
            return result

        def _prepare_reconciliation_partials(self):
            # interfaces_tipo_cambio_compra_venta/models/account_move_line.py
            ''' Prepare the partials on the current journal items to perform the reconciliation.
            /!\ The order of records in self is important because the journal items will be reconciled using this order.

            :return: A recordset of account.partial.reconcile.
            '''

            def fix_remaining_cent(currency, abs_residual, partial_amount):
                if abs_residual - currency.rounding <= partial_amount <= abs_residual + currency.rounding:
                    return abs_residual
                else:
                    return partial_amount

            debit_lines = iter(self.filtered(lambda line: line.balance > 0.0 or line.amount_currency > 0.0 and not line.reconciled))
            credit_lines = iter(self.filtered(lambda line: line.balance < 0.0 or line.amount_currency < 0.0 and not line.reconciled))
            void_lines = iter(self.filtered(lambda line: not line.balance and not line.amount_currency and not line.reconciled))
            debit_line = None
            credit_line = None

            debit_amount_residual = 0.0
            debit_amount_residual_currency = 0.0
            credit_amount_residual = 0.0
            credit_amount_residual_currency = 0.0
            debit_line_currency = None
            credit_line_currency = None

            partials_vals_list = []

            while True:

                # Move to the next available debit line.
                if not debit_line:
                    debit_line = next(debit_lines, None) or next(void_lines, None)
                    if not debit_line:
                        break
                    debit_amount_residual = debit_line.amount_residual

                    if debit_line.currency_id:
                        debit_amount_residual_currency = debit_line.amount_residual_currency
                        debit_line_currency = debit_line.currency_id
                    else:
                        debit_amount_residual_currency = debit_amount_residual
                        debit_line_currency = debit_line.company_currency_id

                # Move to the next available credit line.
                if not credit_line:
                    credit_line = next(void_lines, None) or next(credit_lines, None)
                    if not credit_line:
                        break
                    credit_amount_residual = credit_line.amount_residual

                    if credit_line.currency_id:
                        credit_amount_residual_currency = credit_line.amount_residual_currency
                        credit_line_currency = credit_line.currency_id
                    else:
                        credit_amount_residual_currency = credit_amount_residual
                        credit_line_currency = credit_line.company_currency_id

                min_amount_residual = min(debit_amount_residual, -credit_amount_residual)

                if debit_line_currency == credit_line_currency:
                    # Reconcile on the same currency.

                    min_amount_residual_currency = min(debit_amount_residual_currency, -credit_amount_residual_currency)
                    min_debit_amount_residual_currency = min_amount_residual_currency
                    min_credit_amount_residual_currency = min_amount_residual_currency

                else:
                    # Reconcile on the company's currency.

                    min_debit_amount_residual_currency = credit_line.company_currency_id._convert_tipo_cambio_vendedor(
                        min_amount_residual,
                        debit_line.currency_id,
                        credit_line.company_id,
                        credit_line.date,
                        force_rate=credit_line.move_id.currency_rate
                    )
                    min_debit_amount_residual_currency = fix_remaining_cent(
                        debit_line.currency_id,
                        debit_amount_residual_currency,
                        min_debit_amount_residual_currency,
                    )
                    min_credit_amount_residual_currency = debit_line.company_currency_id._convert_tipo_cambio_vendedor(
                        min_amount_residual,
                        credit_line.currency_id,
                        debit_line.company_id,
                        debit_line.date,
                        force_rate=credit_line.move_id.currency_rate
                    )
                    min_credit_amount_residual_currency = fix_remaining_cent(
                        credit_line.currency_id,
                        -credit_amount_residual_currency,
                        min_credit_amount_residual_currency,
                    )

                debit_amount_residual -= min_amount_residual
                debit_amount_residual_currency -= min_debit_amount_residual_currency
                credit_amount_residual += min_amount_residual
                credit_amount_residual_currency += min_credit_amount_residual_currency

                partials_vals_list.append({
                    'amount': min_amount_residual,
                    'debit_amount_currency': min_debit_amount_residual_currency,
                    'credit_amount_currency': min_credit_amount_residual_currency,
                    'debit_move_id': debit_line.id,
                    'credit_move_id': credit_line.id,
                })

                has_debit_residual_left = not debit_line.company_currency_id.is_zero(debit_amount_residual) and debit_amount_residual > 0.0
                has_credit_residual_left = not credit_line.company_currency_id.is_zero(credit_amount_residual) and credit_amount_residual < 0.0
                has_debit_residual_curr_left = not debit_line_currency.is_zero(debit_amount_residual_currency) and debit_amount_residual_currency > 0.0
                has_credit_residual_curr_left = not credit_line_currency.is_zero(credit_amount_residual_currency) and credit_amount_residual_currency < 0.0

                if debit_line_currency == credit_line_currency:
                    # The debit line is now fully reconciled because:
                    # - either amount_residual & amount_residual_currency are at 0.
                    # - either the credit_line is not an exchange difference one.
                    if not has_debit_residual_curr_left and (has_credit_residual_curr_left or not has_debit_residual_left):
                        debit_line = None

                    # The credit line is now fully reconciled because:
                    # - either amount_residual & amount_residual_currency are at 0.
                    # - either the debit is not an exchange difference one.
                    if not has_credit_residual_curr_left and (has_debit_residual_curr_left or not has_credit_residual_left):
                        credit_line = None

                else:
                    # The debit line is now fully reconciled since amount_residual is 0.
                    if not has_debit_residual_left:
                        debit_line = None

                    # The credit line is now fully reconciled since amount_residual is 0.
                    if not has_credit_residual_left:
                        credit_line = None

            return partials_vals_list
