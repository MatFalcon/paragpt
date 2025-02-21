from odoo import http
from odoo.http import request

class PosTicketController(http.Controller):
    @http.route('/pos/get_invoice_ticket_data', type='json', auth='user')
    def get_invoice_ticket_data(self, pos_order_id):
        """Devuelve los datos del ticket POS vinculado a la factura"""
        pos_order = request.env['pos.order'].browse(pos_order_id)

        if not pos_order.exists():
            return {"error": "No se encontró una orden de POS vinculada a esta factura."}

        ticket_data = {
            "partner_name": pos_order.partner_id.name or "Cliente Genérico",
            "lines": [
                {"product": line.product_id.name, "qty": line.qty, "price": line.price_subtotal}
                for line in pos_order.lines
            ],
            "total": pos_order.amount_total,
        }

        return ticket_data
