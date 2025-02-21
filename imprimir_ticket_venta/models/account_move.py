from odoo import models, api
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_print_pos_ticket(self):
        """Llama a la impresión del ticket POS asociado a la factura"""
        self.ensure_one()

        # Buscar la orden de POS vinculada a la factura
        pos_order = self.env['pos.order'].search([('account_move', '=', self.id)], limit=1)

        if not pos_order:
            raise UserError("No se encontró una orden de POS vinculada a esta factura.")

        # Llamar a la acción de impresión en el frontend
        return {
            'type': 'ir.actions.client',
            'tag': 'print_pos_invoice_ticket_action',
            'context': {'pos_order_id': pos_order.id},
        }
