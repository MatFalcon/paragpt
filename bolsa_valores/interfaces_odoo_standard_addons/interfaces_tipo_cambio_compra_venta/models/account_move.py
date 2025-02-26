from odoo import api, fields, models, _, exceptions, release


class AccountMove(models.Model):
    _inherit = 'account.move'

    currency_rate = fields.Float(string='Tipo de Cambio')
    freeze_currency_rate = fields.Boolean(string='Congelar Tipo de Cambio', default=False)
    count_invoice_line_ids = fields.Integer(compute='_get_count_invoice_line_ids')

    @api.onchange('invoice_line_ids', 'line_ids')
    def _get_count_invoice_line_ids(self):
        # interfaces_tipo_cambio_compra_venta/models/account_move.py
        for this in self:
            this.count_invoice_line_ids = len(this.invoice_line_ids)

    @api.onchange('currency_id', 'invoice_date', 'date')
    def get_tipo_cambio_default(self):
        # interfaces_tipo_cambio_compra_venta/models/account_move.py
        for this in self:
            if this.freeze_currency_rate: continue
            currency_rate = 1
            if this.currency_id:
                _get_conversion_rate = this.currency_id._get_conversion_rate
                if this.move_type in ['out_invoice', 'out_refund', 'in_invoice', 'in_refund']:
                    if this.move_type in ['out_invoice', 'out_refund']:
                        _get_conversion_rate = this.currency_id._get_conversion_rate_tipo_cambio_comprador
                    elif this.move_type in ['in_invoice', 'in_refund']:
                        _get_conversion_rate = this.currency_id._get_conversion_rate_tipo_cambio_vendedor
                currency_rate = _get_conversion_rate(
                    this.currency_id,
                    this.company_id.currency_id,
                    this.company_id,
                    (this.date or this.invoice_date or fields.date.today())
                )
            if this.currency_rate != currency_rate:
                this.currency_rate = currency_rate

    @api.onchange('date', 'currency_id', 'currency_rate')
    def _onchange_currency(self):
        # interfaces_tipo_cambio_compra_venta/models/account_move.py
        self.get_tipo_cambio_default()
        if release.major_version in ['16.0']:
            for this in self:
                for line in this.invoice_line_ids:
                    line.balance = line.company_id.currency_id.round(line.amount_currency / line.currency_rate)
        if release.major_version in ['15.0']:
            result = True
            for this in self.filtered(lambda x: x.state not in ['posted', 'cancel']):
                result = super(AccountMove, this)._onchange_currency()
            return result

    @api.onchange('currency_id')
    def _onchange_currency_with_invoice_lines(self):
        # interfaces_tipo_cambio_compra_venta/models/account_move.py
        if self.invoice_line_ids:
            raise exceptions.ValidationError(_('No es posible cambiar de moneda cuando la factura contiene líneas'))

    @api.onchange('freeze_currency_rate')
    def _onchange_freeze_currency_rate(self):
        # interfaces_tipo_cambio_compra_venta/models/account_move.py
        if not self.freeze_currency_rate:
            self._onchange_currency()

    def action_register_payment(self):
        # interfaces_tipo_cambio_compra_venta/models/account_move.py
        result = super(AccountMove, self).action_register_payment()
        context = result.get('context') or {}

        # Si hay mas de un pago seleccionado, omitimos el currency
        if context and context.get('active_ids') and len(context.get('active_ids')) == 1:
            context.update({
                'default_freeze_currency_rate': self.freeze_currency_rate,
                'default_currency_rate': self.currency_rate,
            })
            result['context'] = context

        return result

    if True and release.major_version in ['16.0']:

        @api.model
        def create(self, vals):
            result = super(AccountMove, self).create(vals)
            for this in result:
                if (this.sale_order_count or this.purchase_order_count) and this.state in ['draft'] and this.line_ids:
                    this._onchange_currency()
                    this.line_ids._compute_currency_rate()
            return result

        # def action_post(self):
        #     for this in self:
        #         this._onchange_currency()
        #     return super().action_post()

    if release.major_version in ['15.0']:

        @api.onchange('invoice_line_ids')
        def _onchange_invoice_line_ids(self):
            # interfaces_tipo_cambio_compra_venta/models/account_move.py
            result = super(AccountMove, self)._onchange_invoice_line_ids()
            for move in self:
                move._onchange_currency()
            return result
