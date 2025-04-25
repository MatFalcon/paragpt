/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";
import { xml } from "@odoo/owl";
import { TicketCambio } from "@pos_paraguay/apps/ticket_cambio/ticket_cambio_template";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        this.printer = useService("printer");
        this.pos = useService("pos");
    },

    async printCustomXML() {
        const order = this.pos.get_order();
        if (!order) {
            console.warn("No hay una orden para imprimir");
            return;
        }

        const orderData = {
            ...order.export_for_printing(),
            es_ticket_cambio: true,
        };

        console.log("📄 Datos del ticket personalizado:", orderData);

        if (!this.printer || typeof this.printer.print !== "function") {
            console.error("El servicio de impresion no esta disponible o no es valido.");
            return;
        }

        try {
            const isPrinted = await this.printer.print(
                TicketCambio,
                {
                    data: orderData,
                    formatCurrency: this.env.utils.formatCurrency,
                },
                { webPrintFallback: true }
            );

            if (!isPrinted) {
                console.warn("⚠️ No se pudo imprimir el ticket.");
            }
        } catch (error) {
            console.error("Error al intentar imprimir el ticket personalizado:", error);
        }
    },

    generateCustomXML(order) {
        return xml`<h1>test</h1>`;
    },
});
