/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
//import { TicketCambio } from "@pos_paraguay/apps/ticket_cambio/ticket_cambio_template";

class AccountTicketPrinter extends Component {
    setup() {
        console.log("Entra en el JS para imprimir el Ticket POS desde Facturas");

        this.rpc = useService("rpc");
        console.log("Servicio RPC inicializado");

        this.state = useState({ orderData: null });
        console.log("Estado inicializado", this.state);

        // Obtener el POS Order ID desde el contexto de la acción
        this.posOrderId = this.props.action.context?.pos_order_id;
        console.log("POS Order ID obtenido:", this.posOrderId);

        if (!this.posOrderId) {
            console.error("No se encontró el ID de la orden POS en el contexto.");
        } else {
            this.loadOrderData();
        }
    }

    async loadOrderData() {
        console.log("Procesando POS Order ID:", this.posOrderId);

        if (!this.posOrderId) {
            return;
        }

        try {
            this.state.orderData = await this.rpc("/pos/get_ticket_data", { pos_order_id: this.posOrderId });
            console.log("Datos del ticket POS obtenidos:", this.state.orderData);
        } catch (error) {
            console.error("Error obteniendo datos del ticket:", error);
        }
    }

    async printCustomTicket() {
        if (!this.state.orderData) {
            console.warn("No hay datos del ticket para imprimir.");
            return;
        }

        console.log("Imprimiendo ticket en el navegador...");

        // Crear una nueva ventana con el contenido del ticket
        const printWindow = window.open("", "_blank");
        printWindow.document.write(`
            <html>
            <head>
                <title>Ticket de Venta</title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    h2 { text-align: center; }
                    .ticket { width: 300px; padding: 10px; border: 1px solid #000; }
                    .line { display: flex; justify-content: space-between; margin-bottom: 5px; }
                </style>
            </head>
            <body>
                <div class="ticket">
                    <h2>Ticket de Venta</h2>
                    <p><strong>Cliente:</strong> ${this.state.orderData.partner_name}</p>
                    <hr>
                    ${this.state.orderData.lines.map(line => `
                        <div class="line">
                            <span>${line.product}</span>
                            <span>${line.qty} x ${line.price}</span>
                        </div>
                    `).join("")}
                    <hr>
                    <p><strong>Total:</strong> ${this.state.orderData.total}</p>
                </div>
                <script>
                    window.onload = function() {
                        window.print();
                        setTimeout(() => window.close(), 100);
                    };
                </script>
            </body>
            </html>
        `);

        printWindow.document.close();
    }

    static template = xml`
        <div>
            <h1>Imprimir Ticket</h1>
            <button class="btn btn-primary" t-on-click="printCustomTicket">Imprimir Ticket POS</button>
        </div>
    `;
}

registry.category("actions").add("print_custom_pos_ticket_action", AccountTicketPrinter);
