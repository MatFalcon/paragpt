/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class SaleTicketPrinter extends Component {
    setup() {
        console.log("Entra en el JS para imprimir Sale Ticket");
        console.log(this)
        this.rpc = useService("rpc");
        console.log("Ejecuto rpc");

        this.state = useState({ orderData: null });
        console.log("State inicializado", this.state);

        // Obtener el Sale Order ID desde el contexto de la acción
        this.saleOrderId = this.props.action.context?.sale_order_id;
        console.log("Sale Order ID obtenido:", this.saleOrderId);

        if (!this.saleOrderId) {
            console.error("No se encontró el ID del pedido en el contexto.");
        } else {
            this.loadOrderData();
        }
    }

    async loadOrderData() {
        console.log("Procesando Sale Order ID:", this.saleOrderId);

        if (!this.saleOrderId) {
            return;
        }

        try {
            this.state.orderData = await this.rpc("/sale/get_ticket_data", { sale_order_id: this.saleOrderId });
            console.log("Datos de la orden obtenidos:", this.state.orderData);
        } catch (error) {
            console.error("Error obteniendo datos del ticket:", error);
        }
    }

    async printSaleTicket() {
        if (!this.state.orderData) {
            console.warn("No hay datos de la orden para imprimir.");
            return;
        }

        console.log("Imprimiendo en el navegador...");

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
                <h1>Test</h1>   
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
            <button class="btn btn-primary" t-on-click="printSaleTicket">Imprimir Ticket</button>
        </div>
    `;
}

registry.category("actions").add("print_sale_ticket_action", SaleTicketPrinter);
