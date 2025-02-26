from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    def create_invoices(self):
        result = super(SaleAdvancePaymentInv, self).create_invoices()
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        for sale_order in sale_orders:
            sale_order.invoice_ids.with_context(check_move_validity=False)._onchange_currency()
        return result
