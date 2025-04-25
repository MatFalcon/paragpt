/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Order } from "@point_of_sale/app/store/models";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PosStore.prototype, {
    getReceiptHeaderData(order) {
        console.log("Iniciando getReceiptHeaderData en pos_order");
        const result = super.getReceiptHeaderData(...arguments);
        console.log("Resultado inicial obtenido de super:", result);
        console.log("Order recibido:", order);
        console.log("Reprint flag:", order.reprint);

        if (order) {
            console.log("Procesando datos del order");
            result.partner = order.get_partner();
            console.log("Partner asignado:", result.partner);
            result.invoice_name = order.invoice_name;
            console.log("Nombre de factura asignado:", result.invoice_name);
            result.timbrado = order.timbrado;
            console.log("Timbrado asignado:", result.timbrado);
            result.fecha_inicio_timbrado = order.fecha_inicio_timbrado;
            console.log("Fecha inicio timbrado asignada:", result.fecha_inicio_timbrado);
            result.fecha_final_timbrado = order.fecha_final_timbrado;
            console.log("Fecha final timbrado asignada:", result.fecha_final_timbrado);
            result.fecha_factura = order.fecha_factura;
            console.log("Fecha de factura asignada:", result.fecha_factura);
            result.totales = order.amount_total;
            console.log("Totales asignados:", result.totales);
            result.move_type = order.move_type;
            console.log("Tipo de movimiento asignado:", result.move_type);
            result.es_facturador_electronico = order.es_facturador_electronico;
            console.log("Es facturador electronico asignado:", result.es_facturador_electronico);
            result.nombre_marca = order.nombre_marca;
            console.log("Nombre de marca asignado:", result.nombre_marca);
            result.tel_personalizado = order.tel_personalizado;
            console.log("Telefono personalizado asignado:", result.tel_personalizado);
            result.descripcion_compania = order.descripcion_compania;
            console.log("Descripcion de compania asignada:", result.descripcion_compania);

            if (order.lineasFactura && Array.isArray(order.lineasFactura)) {
                console.log("Lineas de factura encontradas y son un array");
                result.lineasFactura = order.lineasFactura.map(line => JSON.parse(JSON.stringify(line)));
                console.log("Lineas de factura procesadas:", result.lineasFactura);
            } else {
                console.log("Lineas de factura no definidas o no son un array, asignando array vacio");
                result.lineasFactura = [];
            }
        }

        console.log("Resultado final de getReceiptHeaderData:", result);
        return result;
    },
});

patch(Order.prototype, {
    export_for_printing() {
        console.log("Iniciando export_for_printing en pos_order");
        const result = super.export_for_printing(...arguments);
        console.log("Resultado inicial obtenido de super:", result);

        if (!this.invoice_name || !this.timbrado) {
            console.log("Datos de factura no encontrados, cargando desde PosDB para reimpresion...");
            const savedData = this.pos.db.load('pos_order_' + this.uid);
            console.log("Datos cargados desde PosDB:", savedData);

            if (savedData) {
                this.invoice_name = savedData.invoice_name;
                console.log("Nombre de factura cargado:", this.invoice_name);
                this.timbrado = savedData.timbrado;
                console.log("Timbrado cargado:", this.timbrado);
                this.fecha_inicio_timbrado = savedData.fecha_inicio_timbrado;
                console.log("Fecha inicio timbrado cargada:", this.fecha_inicio_timbrado);
                this.fecha_final_timbrado = savedData.fecha_final_timbrado;
                console.log("Fecha final timbrado cargada:", this.fecha_final_timbrado);
                this.fecha_factura = savedData.fecha_factura;
                console.log("Fecha de factura cargada:", this.fecha_factura);
                this.amount_total = savedData.amount_total;
                console.log("Total cargado:", this.amount_total);
                this.es_facturador_electronico = savedData.es_facturador_electronico;
                console.log("Es facturador electronico cargado:", this.es_facturador_electronico);
                this.nombre_marca = savedData.nombre_marca;
                console.log("Nombre de marca cargado:", this.nombre_marca);
                this.tel_personalizado = savedData.tel_personalizado;
                console.log("Telefono personalizado cargado:", this.tel_personalizado);
                this.descripcion_compania = savedData.descripcion_compania;
                console.log("Descripcion de compania cargada:", this.descripcion_compania);
                this.lineasFactura = savedData.lineasFactura;
                console.log("Lineas de factura cargadas:", this.lineasFactura);
            }
        }

        result.invoice_name = this.invoice_name;
        console.log("Nombre de factura asignado al resultado:", result.invoice_name);
        result.timbrado = this.timbrado;
        console.log("Timbrado asignado al resultado:", result.timbrado);
        result.fecha_inicio_timbrado = this.fecha_inicio_timbrado;
        console.log("Fecha inicio timbrado asignada al resultado:", result.fecha_inicio_timbrado);
        result.fecha_final_timbrado = this.fecha_final_timbrado;
        console.log("Fecha final timbrado asignada al resultado:", result.fecha_final_timbrado);
        result.fecha_factura = this.fecha_factura;
        console.log("Fecha de factura asignada al resultado:", result.fecha_factura);
        result.amount_total = this.amount_total;
        console.log("Total asignado al resultado:", result.amount_total);
        result.es_facturador_electronico = this.es_facturador_electronico;
        console.log("Es facturador electronico asignado al resultado:", result.es_facturador_electronico);
        result.nombre_marca = this.nombre_marca;
        console.log("Nombre de marca asignado al resultado:", result.nombre_marca);
        result.tel_personalizado = this.tel_personalizado;
        console.log("Telefono personalizado asignado al resultado:", result.tel_personalizado);
        result.descripcion_compania = this.descripcion_compania;
        console.log("Descripcion de compania asignada al resultado:", result.descripcion_compania);
        result.lineasFactura = this.lineasFactura || [];
        console.log("Lineas de factura asignadas al resultado:", result.lineasFactura);

        console.log("Resultado final de export_for_printing:", result);
        return result;
    },
});
