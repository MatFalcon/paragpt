/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { useService } from "@web/core/utils/hooks";
import { PaymentTermPopup } from "./payment_term_popup";
import { patch } from "@web/core/utils/patch";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.popup = useService("popup");
        setInterval(() => {
            const order = this.currentOrder;
            // console.log("=== DEBUG CREDIT STATE ===");
            // console.log("payment_term_id:", order.payment_term_id);
            // console.log("payment_term_name:", order.payment_term_name);
            // console.log("is_credit_sale:", order.is_credit_sale);
            // console.log("is_credit_order():", order.is_credit_order());
            // console.log("isCurrentOrderCredit getter:", this.isCurrentOrderCredit);
            // console.log("creditSummary:", this.creditSummary);
            // console.log("========================");
        }, 3000);
    },

    // PROPIEDADES CALCULADAS (getters)
    get isCreditSalesAvailable() {
        const enabled = this.pos.isCreditSalesEnabled();
        const hasTerms = this.pos.getAvailablePaymentTerms().length > 0;
        const hasMethod = !!this.pos.getCreditPaymentMethod();
        
        console.log('Credit availability check:', { enabled, hasTerms, hasMethod });
        return enabled && hasTerms && hasMethod;
    },

    get isCurrentOrderCredit() {
        return this.currentOrder.is_credit_order();
    },

    
    get creditSummary() {
        return this.currentOrder.get_credit_summary();
    },

    // MÉTODO PRINCIPAL PARA INICIAR VENTA A CRÉDITO
    async selectCreditSale() {
        console.log("Iniciando proceso de venta a crédito");
        
        // Validación 1: Verificar disponibilidad
        if (!this.isCreditSalesAvailable) {
            await this.popup.add(ErrorPopup, {
                title: "Ventas a Crédito No Disponibles",
                body: "Las ventas a crédito no están habilitadas o faltan configuraciones."
            });
            return;
        }

        // Validación 2: Cliente requerido
        if (this.pos.require_customer_for_credit && !this.currentOrder.get_partner()) {
            await this.popup.add(ErrorPopup, {
                title: "Cliente Requerido",
                body: "Debe seleccionar un cliente antes de procesar una venta a crédito."
            });
            return;
        }

        // Mostrar popup de términos
        try {
            const { confirmed, payload } = await this.popup.add(PaymentTermPopup, {
                title: "Seleccionar Plazo de Pago",
                payment_terms: this.pos.getAvailablePaymentTerms()
            });

            if (confirmed && payload) {
                await this.processCreditSale(payload);
            }
        } catch (error) {
            console.error("Error en popup de términos:", error);
            await this.popup.add(ErrorPopup, {
                title: "Error",
                body: "Error al mostrar términos de pago."
            });
        }
    },

    // PROCESAR VENTA A CRÉDITO
    async processCreditSale(payload) {
        const order = this.currentOrder;
        
        try {
            // Validar límite de crédito
            const customer = order.get_partner();
            if (customer && this.pos.credit_limit_validation) {
                const validation = await this.pos.validateCustomerCreditLimit(
                    customer, 
                    order.get_total_with_tax()
                );
                
                if (!validation.valid) {
                    await this.popup.add(ErrorPopup, {
                        title: "Límite de Crédito Excedido",
                        body: validation.message
                    });
                    return;
                }
            }

            // Configurar término de pago
            order.set_payment_term(payload.payment_term_id, payload.payment_term_name);

            // Aplicar método de pago automáticamente
            const success = order.apply_credit_payment_method();
            
            if (!success) {
                await this.popup.add(ErrorPopup, {
                    title: "Error de Configuración",
                    body: "No se pudo aplicar el método de pago de crédito."
                });
                order.clear_payment_term();
                return;
            }

            console.log(`Venta a crédito configurada: ${payload.payment_term_name}`);

        } catch (error) {
            console.error("Error procesando venta a crédito:", error);
            await this.popup.add(ErrorPopup, {
                title: "Error",
                body: "Ocurrió un error al procesar la venta a crédito."
            });
            order.clear_payment_term();
        }
    },

    // CANCELAR VENTA A CRÉDITO
    async cancelCreditSale() {
        const { confirmed } = await this.popup.add(ConfirmPopup, {
            title: "Cancelar Venta a Crédito",
            body: "¿Cancelar la venta a crédito y volver a venta normal?"
        });

        if (confirmed) {
            this.currentOrder.clear_payment_term();
            
            // Limpiar pagos de crédito
            const creditMethod = this.pos.getCreditPaymentMethod();
            if (creditMethod) {
                const creditPayments = this.currentOrder.paymentlines.filter(
                    payment => payment.payment_method.id === creditMethod.id
                );
                
                creditPayments.forEach(payment => {
                    this.currentOrder.remove_paymentline(payment);
                });
            }
        }
    },

    // VALIDACIÓN ANTES DE CONFIRMAR ORDEN
    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        
        // Validaciones para ventas a crédito
        if (order.is_credit_order()) {
            const validation = order.validate_credit_order();
            
            if (!validation.valid) {
                await this.popup.add(ErrorPopup, {
                    title: "Error de Validación",
                    body: validation.message
                });
                return false;
            }

            // Re-validar límite de crédito
            const customer = order.get_partner();
            if (customer && this.pos.credit_limit_validation) {
                const creditValidation = await this.pos.validateCustomerCreditLimit(
                    customer, 
                    order.get_total_with_tax()
                );
                
                if (!creditValidation.valid) {
                    await this.popup.add(ErrorPopup, {
                        title: "Límite de Crédito Excedido",
                        body: creditValidation.message
                    });
                    return false;
                }
            }
        }

        return super.validateOrder(isForceValidate);
    },



    // === MÉTODOS PARA LA VISTA DE ESTADO DE CRÉDITO ===

    // Formatear moneda
    formatCurrency(amount) {
        return this.pos.format_currency(amount || 0);
    },

    // Obtener crédito disponible del cliente
    getAvailableCredit() {
        const partner = this.currentOrder.get_partner();
        if (!partner || !partner.credit_limit) {
            return 0;
        }
        return partner.credit_limit - (partner.credit || 0);
    },

    // Verificar si se excede el límite de crédito
    isCreditLimitExceeded() {
        const partner = this.currentOrder.get_partner();
        if (!partner || !partner.credit_limit) {
            return false;
        }
        
        const orderTotal = this.currentOrder.get_total_with_tax();
        const availableCredit = this.getAvailableCredit();
        return orderTotal > availableCredit;
    },

    // Obtener cantidad que excede el límite
    getCreditExcess() {
        if (!this.isCreditLimitExceeded()) {
            return 0;
        }
        
        const orderTotal = this.currentOrder.get_total_with_tax();
        const availableCredit = this.getAvailableCredit();
        return orderTotal - availableCredit;
    },

    // Estilo para el límite de crédito
    getCreditLimitStyle() {
        const partner = this.currentOrder.get_partner();
        if (!partner || !partner.credit_limit) {
            return "color: #ff9800; font-style: italic;";
        }
        return "font-weight: bold; color: #4caf50;";
    },

    // Estilo para el crédito disponible
    getAvailableCreditStyle() {
        if (this.isCreditLimitExceeded()) {
            return "color: #f44336; font-weight: bold;";
        }
        
        const partner = this.currentOrder.get_partner();
        if (!partner || !partner.credit_limit) {
            return "color: #4caf50; font-weight: bold;";
        }
        
        const availableCredit = this.getAvailableCredit();
        const orderTotal = this.currentOrder.get_total_with_tax();
        
        // Alerta si queda poco crédito disponible
        if (availableCredit - orderTotal < orderTotal * 0.1) {
            return "color: #ff9800; font-weight: bold;";
        }
        
        return "color: #4caf50; font-weight: bold;";
    }
});