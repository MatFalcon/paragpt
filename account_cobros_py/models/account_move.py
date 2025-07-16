# -*- coding: utf-8 -*-
import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)

class FacturaInvoice(models.Model):
    _inherit = 'account.move'

    no_ver_factura_recibo = fields.Boolean(default=False, store=True)
    recibo_id = fields.Many2one('account.recibo', string="Recibo")
    recibos_vinculados_ids = fields.One2many(
        'account.recibo',
        'invoice_ids',
        string="Recibos Vinculados",
        compute='_compute_recibos_vinculados',
        store=False
    )
    recibos_vinculados_count = fields.Integer(
        string="Recibos",
        compute="_compute_recibos_vinculados_count"
    )

    @api.depends('line_ids')
    def _compute_recibos_vinculados(self):
        """Compute linked receipts (recibos) for the invoice."""
        for move in self:
            _logger.info(f"Computando recibos vinculados para la factura ID: {move.id}")
            recibos = self.env['account.recibo'].search([
                ('pagos_facturas_ids.invoice_id', '=', move.id)
            ])
            _logger.info(f"Recibos encontrados para la factura {move.id}: {recibos.ids}")
            move.recibos_vinculados_ids = recibos

    @api.depends('recibos_vinculados_ids')
    def _compute_recibos_vinculados_count(self):
        """Compute the count of linked receipts."""
        for move in self:
            count = len(move.recibos_vinculados_ids)
            _logger.info(f"Recibos vinculados contados para la factura ID {move.id}: {count}")
            move.recibos_vinculados_count = count

    def action_open_recibos_vinculados(self):
        """Action to open the linked receipts."""
        self.ensure_one()
        _logger.info(f"Abrir recibos vinculados para la factura ID: {self.id}")
        return {
            'name': 'Recibos Vinculados',
            'type': 'ir.actions.act_window',
            'res_model': 'account.recibo',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.recibos_vinculados_ids.ids)],
            'context': {'create': False},
        }


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    recibo_pago_factura = fields.One2many(
        'account.pago.factura',
        'move_line_id',
        string="Líneas de recibo"
    )
    recibo_id = fields.Many2one(
        related="recibo_pago_factura.recibo_id",
        store=True,
        string="Recibo"
    )

    def _compute_amount_currency(self):
        # _logger.warning('compute custom %s', self)
        for line in self:
            pago = line.move_id.payment_id
            if pago.moneda_pago != self.env.company.currency_id:
                # _logger.warning('pago %s', pago)
                if pago.moneda_pago and pago.moneda_pago != pago.currency_id:
                    # _logger.warning('pago moneda %s', pago.moneda_pago)
                    # _logger.warning('line %s amount currency %s',line, line.amount_currency)
                    # _logger.warning('pago moneda pago %s, pago monto moneda pago %s', pago.moneda_pago, pago.monto_moneda_pago)
                    if pago.monto_moneda_pago:
                        updated_lines = [
                            (
                                1,
                                line.id,
                                {
                                    'amount_currency': pago.monto_moneda_pago if line.debit > 0 else -pago.monto_moneda_pago,
                                    'currency_id': pago.moneda_pago.id,
                                    'balance': line.balance
                                }
                            )
                            for line in line.move_id.line_ids
                        ]
                        # _logger.warning("updated %s", updated_lines)
        
                        line.move_id.with_context(skip_account_move_synchronization=True).write(
                            {'currency_id': pago.moneda_pago.id, 'line_ids': updated_lines})

        return super(AccountMoveLine, self)._compute_amount_currency()
