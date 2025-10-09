    /** @odoo-module */

import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

// Extender el modelo Order para incluir funcionalidad de crédito
patch(Order.prototype, {
    setup(_defaultObj, options) {
        super.setup(...arguments);
        this.payment_term_id = this.payment_term_id || null;
        this.payment_term_name = this.payment_term_name || null;
        this.is_credit_sale = this.is_credit_sale || false;
    },

    // Establecer término de pago
    set_payment_term: function(term_id, term_name) {
        this.payment_term_id = term_id;
        this.payment_term_name = term_name;
        this.is_credit_sale = true;
    },

    // Obtener término de pago
    get_payment_term() {
        return {
            id: this.payment_term_id,
            name: this.payment_term_name
        };
    },

    // Verificar si es venta a crédito
    is_credit_order() {
        return this.is_credit_sale && this.payment_term_id;
    },

    // Limpiar término de pago (volver a venta normal)
    clear_payment_term() {
        this.payment_term_id = null;
        this.payment_term_name = null;
        this.is_credit_sale = false;
        // this.trigger('change', this);
    },

    // Exportar datos para el backend
    export_as_JSON() {
        const json = super.export_as_JSON();
        json.payment_term_id = this.payment_term_id;
        json.payment_term_name = this.payment_term_name;
        json.is_credit_sale = this.is_credit_sale;
        return json;
    },

    // Inicializar desde JSON
    init_from_JSON(json) {
        super.init_from_JSON(json);
        this.payment_term_id = json.payment_term_id || null;
        this.payment_term_name = json.payment_term_name || null;
        this.is_credit_sale = json.is_credit_sale || false;
    },

    // Validar orden antes de confirmar
    validate_credit_order() {
        if (!this.is_credit_order()) {
            return { valid: true };
        }

        // Verificar que tiene cliente si es requerido
        if (this.pos.require_customer_for_credit && !this.get_partner()) {
            return {
                valid: false,
                message: "Debe seleccionar un cliente para las ventas a crédito."
            };
        }

        // Verificar que tiene el método de pago correcto
        const creditMethod = this.pos.getCreditPaymentMethod();
        if (creditMethod) {
            const hasCreditPayment = this.paymentlines.some(
                payment => payment.payment_method.id === creditMethod.id
            );
            
            if (!hasCreditPayment) {
                return {
                    valid: false,
                    message: "Debe usar el método de pago 'Cuenta de Cliente' para ventas a crédito."
                };
            }
        }

        return { valid: true };
    },

    // Aplicar método de pago de crédito automáticamente
    apply_credit_payment_method() {
        const creditMethod = this.pos.getCreditPaymentMethod();
        if (!creditMethod) {
            console.warn('No hay método de pago de crédito configurado');
            return false;
        }

        // Limpiar pagos existentes
        this.paymentlines.forEach(payment => {
            this.remove_paymentline(payment);
        });

        // Agregar línea de pago de crédito
        const total = this.get_total_with_tax();
        const paymentLine = this.add_paymentline(creditMethod);
        paymentLine.set_amount(total);
        
        return true;
    },

    // Obtener información de resumen para UI
    get_credit_summary() {
        if (!this.is_credit_order()) {
            return null;
        }

        return {
            payment_term: this.payment_term_name,
            customer: this.get_partner()?.name || 'Sin cliente',
            amount: this.get_total_with_tax(),
            formatted_amount: this.get_total_with_tax()
            // formatted_amount: this.pos.format_currency(this.get_total_with_tax())
        };
    }
});