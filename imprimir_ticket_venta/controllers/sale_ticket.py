from odoo import http
from odoo.http import request

class SaleTicketController(http.Controller):
    @http.route('/sale/get_ticket_data', type='json', auth='user')
    def get_ticket_data(self, sale_order_id):
        sale_order = request.env['sale.order'].browse(sale_order_id)
        if not sale_order.exists():
            return {"error": "Pedido de venta no encontrado"}

        ticket_data = {
            "partner_name": sale_order.partner_id.name,
            "lines": [
                {"product": line.product_id.name, "qty": line.product_uom_qty, "price": line.price_total}
                for line in sale_order.order_line
            ],
            "total": sale_order.amount_total,
        }
        return ticket_data
