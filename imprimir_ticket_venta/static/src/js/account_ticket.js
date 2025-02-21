/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class AccountTicketPrinter extends Component {
    setup() {
        console.log("Entra en el JS para imprimir el Ticket POS desde Facturas");

        this.rpc = useService("rpc");
        this.state = useState({ orderData: null });

        this.posOrderId = this.props.action.context?.pos_order_id;
        console.log("POS Order ID obtenido:", this.posOrderId);

        if (this.posOrderId) {
            this.loadOrderData();
        }
    }

    async loadOrderData() {
        try {
            this.state.orderData = await this.rpc("/pos/get_invoice_ticket_data", { pos_order_id: this.posOrderId });
            console.log("Datos del ticket POS obtenidos:", this.state.orderData);
        } catch (error) {
            console.error("Error obteniendo datos del ticket:", error);
        }
    }

    async printTicket() {
        if (!this.state.orderData) {
            console.warn("No hay datos del ticket para imprimir.");
            return;
        }

        console.log("Imprimiendo ticket en el navegador...");

        const printWindow = window.open("", "_blank");
        printWindow.document.write(`
            <html>
            <head>
                <title>Ticket de Venta</title>
                <style> body { font-family: Arial, sans-serif; } </style>
            </head>
            <body>
                <h2>Ticket de Venta</h2>
                <p>Cliente: ${this.state.orderData.partner_name}</p>
                <ul>
                    ${this.state.orderData.lines.map(line => `<li>${line.product} - ${line.qty} x ${line.price}</li>`).join("")}
                </ul>
                <p>Total: ${this.state.orderData.total}</p>
                <script> window.print(); setTimeout(() => window.close(), 100); </script>
            </body>
            </html>
        `);
        printWindow.document.close();
    }

    static template = xml`
        <div>
            <button class="btn btn-primary" t-on-click="printTicket">Imprimir Ticket POS</button>
        </div>
    `;
}

registry.category("actions").add("print_pos_invoice_ticket_action", AccountTicketPrinter);
