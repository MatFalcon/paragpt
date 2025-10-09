    /** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        
        // Cargar configuración de crédito
        const creditConfig = loadedData['pos_credit_config'] || {};
        
        this.allow_credit_sales = creditConfig.allow_credit_sales || false;
        this.payment_terms = creditConfig.payment_terms || [];
        this.credit_payment_method = creditConfig.credit_payment_method || null;
        this.require_customer_for_credit = creditConfig.require_customer_for_credit || false;
        this.credit_limit_validation = creditConfig.credit_limit_validation || false;
        
        // Cargar términos de pago si están disponibles
        if (loadedData['account.payment.term']) {
            this.payment_terms = loadedData['account.payment.term'];
        }
        
        console.log('Credit config loaded:', {
            allow_credit_sales: this.allow_credit_sales,
            payment_terms: this.payment_terms.length,
            credit_payment_method: this.credit_payment_method?.name
        });
    },

    // Obtener términos de pago disponibles
    getAvailablePaymentTerms() {
        return this.payment_terms || [];
    },

    // Obtener método de pago de crédito
    getCreditPaymentMethod() {
        if (!this.credit_payment_method) {
            return null;
        }
        
        // Buscar el método en los métodos disponibles
        return this.payment_methods.find(
            method => method.id === this.credit_payment_method.id
        );
    },

    // Verificar si las ventas a crédito están habilitadas
    isCreditSalesEnabled() {
        return this.allow_credit_sales;
    },

    // Validar límite de crédito del cliente
    async validateCustomerCreditLimit(customer, orderTotal) {
        if (!this.credit_limit_validation || !customer) {
            return { valid: true };
        }

        const availableCredit = customer.credit_limit - customer.credit;
        
        if (orderTotal > availableCredit) {
            return {
                valid: false,
                message: `El cliente ${customer.name} excede su límite de crédito.\n` +
                        `Límite: ${this.format_currency(customer.credit_limit)}\n` +
                        `Crédito usado: ${this.format_currency(customer.credit)}\n` +
                        `Disponible: ${this.format_currency(availableCredit)}\n` +
                        `Monto de la orden: ${this.format_currency(orderTotal)}`
            };
        }

        return { valid: true };
    }
});