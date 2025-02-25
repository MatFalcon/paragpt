/** @odoo-module */

import { Order, Orderline } from "@point_of_sale/app/store/models";
import { Mutex } from "@web/core/utils/concurrency";
import { roundDecimals, roundPrecision } from "@web/core/utils/numbers";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { PosDB } from "@point_of_sale/app/store/db";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { PartnerDetailsEdit } from "@point_of_sale/app/screens/partner_list/partner_editor/partner_editor";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(Orderline.prototype, {
    get_taxes() {

        if (!this.tax_ids) {

            this.tax_ids=this.order.pos.company.account_sale_tax_id;

            }

        return super.get_taxes(...arguments);
    },
});

// Extensión de la pantalla de pago para manejar facturas y líneas de productos
patch(PaymentScreen.prototype, {
    shouldDownloadInvoice() {
        return false;
    },
    async _postPushOrderResolve(order, order_server_ids) {
     console.log("Se ejecuta _postPushOrderResolve en models pos_paraguay");
        console.log("Inicio del procesamiento del pedido guardado");
        console.log(order);


        // Recuperar el pedido guardado en el backend
        const savedOrder = await this.orm.searchRead(
            "pos.order",
            [["id", "in", order_server_ids]],
            ["account_move", "es_facturador_electronico", "nombre_marca", "tel_personalizado", "descripcion_compania"]
        );

        if (savedOrder.length > 0 && savedOrder[0].account_move) {
            const facturaId = savedOrder[0].account_move[0];

            const fact_gen = await this.orm.searchRead(
                "account.move",
                [["id", "=", facturaId]],
                ["timbrado", "fecha_inicio_timbrado", "fecha_final_timbrado", "nro_factura", "date_invoice", "amount_total","move_type"]
            );

            const lineasFactura = await this.orm.searchRead(
                "account.move.line",
                [["move_id", "=", facturaId], ["product_id", "!=", false]],
                ["product_id", "name", "quantity", "price_unit", "price_total", "tax_name", "nombre_ticket", "cod_barra", "talla"]
            );

            // Almacenar los datos en el objeto `Order`
            order.invoice_name = fact_gen[0].nro_factura;
            order.timbrado = fact_gen[0].timbrado;
            order.fecha_inicio_timbrado = fact_gen[0].fecha_inicio_timbrado;
            order.fecha_final_timbrado = fact_gen[0].fecha_final_timbrado;
            order.fecha_factura = fact_gen[0].date_invoice;
            order.move_type = fact_gen[0].move_type;
            order.lineasFactura = lineasFactura;
            order.amount_total = fact_gen[0].amount_total;
            order.es_facturador_electronico = savedOrder[0].es_facturador_electronico;
            order.nombre_marca = savedOrder[0].nombre_marca;
            order.tel_personalizado = savedOrder[0].tel_personalizado;
            order.descripcion_compania = savedOrder[0].descripcion_compania;

            // Guardar solo los datos personalizados en `PosDB`
            const orderData = {
                invoice_name: order.invoice_name,
                timbrado: order.timbrado,
                fecha_inicio_timbrado: order.fecha_inicio_timbrado,
                fecha_final_timbrado: order.fecha_final_timbrado,
                fecha_factura: order.fecha_factura,
                move_type: order.move_type,
                lineasFactura: order.lineasFactura,
                amount_total: order.amount_total,
                es_facturador_electronico: order.es_facturador_electronico,
                nombre_marca: order.nombre_marca,
                tel_personalizado: order.tel_personalizado,
                descripcion_compania: order.descripcion_compania,
            };

            // para hacer como un store true de la venta
            this.pos.db.save('pos_order_' + order.uid, orderData);
        }

        return super._postPushOrderResolve(...arguments);
    },
});

// Validaciones adicionales para datos de cliente
patch(PartnerDetailsEdit.prototype, {
    saveChanges() {
        console.log("Se ejecuta PartnerDetailsEdit en models pos_paraguay");
        if (this.changes.ruc.includes("-")) {
            return this.popup.add(ErrorPopup, {
                title: _t("ERROR"),
                body: _t("El RUC o CI no debe llevar guion (-)"),
            });
        }
        super.saveChanges();
    },
    setup() {
        super.setup(...arguments);
        this.changes.ruc = this.props.partner.ruc || null;
    },
});

// Mejora en la busqueda de socios en el POS
patch(PosDB.prototype, {
    _partner_search_string(partner) {
        console.log("Se ejecuta _partner_search_string en mo    dels pos_paraguay");
        var str = super._partner_search_string(partner);
        if (partner.ref) {
            str = str.substr(0, str.length - 1) + "|" + partner.rucdv + "\n";
        }
        return str;
    },
});

// Configuracion inicial del pedido
patch(Order.prototype, {
    setup() {
        super.setup(...arguments);
        this.to_invoice = true; // Configurar para facturación por defecto
    },
    wait_for_push_order() {
        return true; // Esperar siempre por la sincronización del pedido
    },
});

// Adiciones para manejar eventos de pantalla
patch(PaymentScreen.prototype, {
    renderElement() {

        super.renderElement();
        console.log("Se ejecuta PaymentScreen en models pos_paraguay");
//        console.log("Renderizando PaymentScreen");
    },
});
