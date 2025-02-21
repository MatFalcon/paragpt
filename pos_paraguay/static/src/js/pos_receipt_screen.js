/** @odoo-module **/

import { useService } from "@web/core/utils/hooks";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { patch } from "@web/core/utils/patch";
import { useState, Component, xml } from "@odoo/owl";
import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { TicketCambio } from "@pos_paraguay/apps/ticket_cambio/ticket_cambio_template";
patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        this.printer = useService("printer");  // Usa el servicio correcto
        this.pos = useService("pos"); // Servicio POS para acceder a la orden
    },

    async printCustomXML() {
        const order = this.pos.get_order();
        if (!order) {
            console.warn("No hay una orden para imprimir");
            return;
        }

        if (!this.printer) {
            console.error("El servicio de impresión no está disponible.");
            return;
        }

        // Verifica que el servicio de impresión tiene la función print_receipt
        if (typeof this.printer.print !== "function") {
            console.error("El servicio de impresión no tiene la función print_receipt.");
            return;
        }
        console.log("Se trata de imprimir");
         const isPrinted = await this.printer.print(
            TicketCambio,
            {
                data: this.pos.get_order().export_for_printing(),
                formatCurrency: this.env.utils.formatCurrency,
            },
            { webPrintFallback: true }
        )

    },
,
});
