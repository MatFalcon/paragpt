/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order } from "@point_of_sale/app/store/models";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PosStore.prototype, {
    getReceiptHeaderData(order) {
        console.log("Se ejecuta getReceiptHeaderData en pos_order");
        const result = super.getReceiptHeaderData(...arguments);
        console.log("Order:", order);
        console.log("Rerprint:", order.reprint);

        /* Para las reimpresiones */
//        if (order.reprint){
//            account_move_id = order.account_move_id;
//        }

        if (order) {
            result.partner = order.get_partner();
            result.invoice_name = order.invoice_name;
            result.timbrado = order.timbrado;
            result.fecha_inicio_timbrado = order.fecha_inicio_timbrado;
            result.fecha_final_timbrado = order.fecha_final_timbrado;
            result.fecha_factura = order.fecha_factura;
            result.totales = order.amount_total;
            result.move_type = order.move_type;
            result.es_facturador_electronico = order.es_facturador_electronico;
            result.nombre_marca = order.nombre_marca;
            result.tel_personalizado = order.tel_personalizado;
            result.descripcion_compania = order.descripcion_compania;

            // Validar la existencia de lineasFactura
            if (order.lineasFactura && Array.isArray(order.lineasFactura)) {
                result.lineasFactura = order.lineasFactura.map(line => JSON.parse(JSON.stringify(line)));
//                console.log("Lineas Factura (como lista):", result.lineasFactura);
            } else {
//                console.warn("lineasFactura no está definido o no es un array.");
                result.lineasFactura = [];
            }
        }

//        console.log("Primer elemento:", result.es_facturador_electronico);
//        console.log("Result:", result);
        return result;
    },
});

patch(Order.prototype, {
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        console.log("Se ejecuta export_for_printing en pos_order");
//        console.log("Llamada a export_for_printing. Lineas Factura mi modulo:", this.lineasFactura);
// Verificar si ya existen los datos en la orden
        if (!this.invoice_name || !this.timbrado) {
            console.log("Cargando datos desde PosDB para reimpresión...");
            const savedData = this.pos.db.load('pos_order_' + this.uid);

            if (savedData) {
                this.invoice_name = savedData.invoice_name;
                this.timbrado = savedData.timbrado;
                this.fecha_inicio_timbrado = savedData.fecha_inicio_timbrado;
                this.fecha_final_timbrado = savedData.fecha_final_timbrado;
                this.fecha_factura = savedData.fecha_factura;
                this.amount_total = savedData.amount_total;
                this.es_facturador_electronico = savedData.es_facturador_electronico;
                this.nombre_marca = savedData.nombre_marca;
                this.tel_personalizado = savedData.tel_personalizado;
                this.descripcion_compania = savedData.descripcion_compania;
                this.lineasFactura = savedData.lineasFactura;
            }
        }

        result.invoice_name = this.invoice_name;
        result.timbrado = this.timbrado;
        result.fecha_inicio_timbrado = this.fecha_inicio_timbrado;
        result.fecha_final_timbrado = this.fecha_final_timbrado;
        result.fecha_factura = this.fecha_factura;
        result.amount_total = this.amount_total;
        result.es_facturador_electronico = this.es_facturador_electronico;
        result.nombre_marca = this.nombre_marca;
        result.tel_personalizado = this.tel_personalizado;
        result.descripcion_compania = this.descripcion_compania;
        result.lineasFactura = this.lineasFactura || [];

        return result;
    },
});
