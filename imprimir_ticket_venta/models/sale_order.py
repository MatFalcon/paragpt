from odoo import models, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'account.move'

    def action_print_sale_ticket(self):
        """Llama a la función en JavaScript para imprimir el ticket"""
        self.ensure_one()
        order_relacionada = self.env["pos.order"].search([('account_move', '=', self.id)])
        # Puedes usar un reporte existente o llamar a una acción de JS
        print("Self:", order_relacionada)
        return {
            'type': 'ir.actions.client',
            'tag': 'print_sale_ticket_action',
            'context': {'sale_order_id': order_relacionada.id},
        }

    def action_print_custom_ticket(self):
        """Llama a la reimpresión del ticket POS personalizado"""
        self.ensure_one()

        # Buscar la orden POS vinculada a la factura
        pos_order = self.env['pos.order'].search([('account_move', '=', self.id)], limit=1)

        if not pos_order:
            raise UserError("No se encontró una orden de POS vinculada a esta factura.")

        # Llamar a la acción de impresión personalizada
        return {
            'type': 'ir.actions.client',
            'tag': 'print_custom_pos_ticket_action',
            'context': {'pos_order_id': pos_order.id},
        }