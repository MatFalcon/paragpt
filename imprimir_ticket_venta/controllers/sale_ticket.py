from odoo import http
from odoo.http import request

class SaleTicketController(http.Controller):
    @http.route('/sale/get_ticket_data', type='json', auth='user')
    def get_ticket_data(self, sale_order_id):
        print("Buscando la orden de POS vinculada a la factura:", sale_order_id)

        # Buscar la orden de punto de venta vinculada a la factura (account.move)
        pos_order = request.env['pos.order'].search([('account_move', '=', sale_order_id)], limit=1)

        if not pos_order:
            return {"error": "No se encontró una orden de POS vinculada a esta factura."}

        # Extraer la información de los productos desde pos.order.line
        ticket_data = {
            "partner_name": pos_order.partner_id.name if pos_order.partner_id else "Cliente Genérico",
            "lines": [
                {"product": line.product_id.name, "qty": line.qty, "price": line.price_subtotal}
                for line in pos_order.lines  # 'lines' es el campo correcto en POS
            ],
            "total": pos_order.amount_total,
        }

        print("Ticket data generado:", ticket_data)
        return ticket_data


class PosTicketController(http.Controller):
    @http.route('/pos/get_ticket_data', type='json', auth='user')
    def get_ticket_data(self, pos_order_id):
        print("Buscando la orden de POS vinculada a la factura:", pos_order_id)

        # Buscar la orden POS
        pos_order = request.env['pos.order'].browse(pos_order_id)

        if not pos_order.exists():
            return {"error": "No se encontró una orden de POS vinculada a esta factura."}

        # Extraer información de los productos desde pos.order.line
        ticket_data = {
            "partner_name": pos_order.partner_id.name if pos_order.partner_id else "Cliente Genérico",
            "lines": [
                {"product": line.product_id.name, "qty": line.qty, "price": line.price_subtotal}
                for line in pos_order.lines
            ],
            "total": pos_order.amount_total,
        }

        print("Ticket data generado:", ticket_data)
        return ticket_data