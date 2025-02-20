from odoo import models, api
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'account.move'

    def action_print_sale_ticket(self):
        """Llama a la función en JavaScript para imprimir el ticket"""
        self.ensure_one()

        # Puedes usar un reporte existente o llamar a una acción de JS
        print("")
        return {
            'type': 'ir.actions.client',
            'tag': 'print_sale_ticket_action',
            'context': {'sale_order_id': self.id},
        }
