from odoo import api, fields, models, release


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    currency_rate = fields.Float(string='Tipo de Cambio')
    freeze_currency_rate = fields.Boolean(string='Congelar Tipo de Cambio', default=False)

    @api.onchange('currency_id', 'payment_date')
    def get_tipo_cambio_default(self):
        # interfaces_tipo_cambio_compra_venta/models/account_payment_register.py
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
                (self.payment_date or fields.date.today())
            )
        if self.currency_rate != currency_rate:
            self.currency_rate = currency_rate

    @api.onchange('date', 'currency_id', 'currency_rate')
    def _onchange_currency(self):
        # interfaces_tipo_cambio_compra_venta/models/account_payment_register.py
        self.get_tipo_cambio_default()

    @api.onchange('freeze_currency_rate')
    def _onchange_freeze_currency_rate(self):
        # interfaces_tipo_cambio_compra_venta/models/account_payment_register.py
        if not self.freeze_currency_rate:
            self._onchange_currency()

    def _create_payment_vals_from_wizard(self, batch_result=False):
        # interfaces_tipo_cambio_compra_venta/models/account_payment_register.py
        payment_vals = {}
        if release.major_version in ['16.0']:
            payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard(batch_result)
            conversion_rate = self.env['res.currency']._get_conversion_rate(
                self.currency_id,
                self.company_id.currency_id,
                self.company_id,
                self.payment_date,
            )
            if self.currency_rate: conversion_rate = self.currency_rate

            if self.payment_difference_handling == 'reconcile':

                if self.early_payment_discount_mode:
                    pass
                elif not self.currency_id.is_zero(self.payment_difference):
                    if self.payment_type == 'inbound':
                        # Receive money.
                        write_off_amount_currency = self.payment_difference
                    else:  # if self.payment_type == 'outbound':
                        # Send money.
                        write_off_amount_currency = -self.payment_difference

                    write_off_balance = self.company_id.currency_id.round(write_off_amount_currency * conversion_rate)
                    payment_vals['write_off_line_vals'] = []
                    payment_vals['write_off_line_vals'].append({
                        'name': self.writeoff_label,
                        'account_id': self.writeoff_account_id.id,
                        'partner_id': self.partner_id.id,
                        'currency_id': self.currency_id.id,
                        'amount_currency': write_off_amount_currency,
                        'balance': write_off_balance,
                    })

        if release.major_version in ['15.0']:
            payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        payment_vals.update({
            'freeze_currency_rate': self.freeze_currency_rate,
            'currency_rate': self.currency_rate,
        })
        return payment_vals

    if release.major_version in ['16.0']:
        def _get_total_amount_in_wizard_currency_to_full_reconcile(self, batch_result, early_payment_discount=True):
            result = super(AccountPaymentRegister, self)._get_total_amount_in_wizard_currency_to_full_reconcile(batch_result, early_payment_discount)
            comp_curr = self.company_id.currency_id
            if self.source_currency_id != self.currency_id and self.source_currency_id != comp_curr and self.currency_id == comp_curr:
                residual_amount = 0
                for aml in batch_result['lines']:
                    residual_amount += aml.amount_residual
                return abs(residual_amount), False
            return result

    if release.major_version in ['15.0']:
        @api.depends('source_amount', 'source_amount_currency', 'source_currency_id', 'company_id', 'currency_id', 'payment_date')
        def _compute_amount(self):
            result = super()._compute_amount()
            for wizard in self:
                if wizard.currency_id == wizard.company_id.currency_id:
                    wizard.amount = wizard.source_amount
            return result
