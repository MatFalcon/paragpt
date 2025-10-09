/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useState } from "@odoo/owl";

export class PaymentTermPopup extends AbstractAwaitablePopup {
    static template = "pos_credit_sales.PaymentTermPopup";
    static defaultProps = {
        confirmText: "Confirmar",
        cancelText: "Cancelar",
        title: "Seleccionar Plazo de Pago",
        body: "",
    };

    // static props = {
    //     ...AbstractAwaitablePopup.props,
    //     payment_terms: { type: Array, optional: true },
    // };
    
    setup() {
        super.setup();
        this.state = useState({
            selectedPaymentTerm: null,
            searchTerm: "",
        });
    }

    // Obtener términos de pago filtrados
    get filteredPaymentTerms() {
        const terms = this.props.payment_terms || [];
        
        if (!this.state.searchTerm) {
            return terms;
        }

        const search = this.state.searchTerm.toLowerCase();
        return terms.filter(term => 
            term.name.toLowerCase().includes(search) ||
            (term.note && term.note.toLowerCase().includes(search))
        );
    }

    // Seleccionar término de pago
    selectPaymentTerm(term) {
        console.log("Selecting payment term:", term);
        console.log("Current state:", this.state);
        
        if (!this.state) {
            console.error("State is undefined!");
            return;
        }
        
        this.state.selectedPaymentTerm = term;
        console.log("Selected term:", this.state.selectedPaymentTerm);
    }

    // Verificar si un término está seleccionado
    isTermSelected(term) {
        return this.state.selectedPaymentTerm?.id === term.id;
    }

    // Manejar búsqueda
    onSearchInput(event) {
        this.state.searchTerm = event.target.value;
    }

    // Obtener payload para confirmar
    getPayload() {
        if (!this.state.selectedPaymentTerm) {
            return null;
        }

        return {
            payment_term_id: this.state.selectedPaymentTerm.id,
            payment_term_name: this.state.selectedPaymentTerm.name,
            payment_term: this.state.selectedPaymentTerm
        };
    }

    // Formatear días del término de pago
    formatPaymentTermDays(term) {
        if (!term.line_ids || term.line_ids.length === 0) {
            return "Inmediato";
        }

        const maxDays = Math.max(...term.line_ids.map(line => line.days || 0));
        
        if (maxDays === 0) {
            return "Inmediato";
        } else if (maxDays === 1) {
            return "1 día";
        } else {
            return `${maxDays} días`;
        }
    }

    // Formatear descripción del término
    formatPaymentTermDescription(term) {
        if (term.note) {
            return term.note;
        }

        if (!term.line_ids || term.line_ids.length === 0) {
            return "Pago inmediato";
        }

        // Generar descripción basada en las líneas
        const descriptions = term.line_ids.map(line => {
            const days = line.days || 0;
            const percentage = line.value_amount || 100;
            
            if (days === 0) {
                return percentage === 100 ? "Pago inmediato" : `${percentage}% inmediato`;
            } else {
                return percentage === 100 ? 
                    `Pago a ${days} días` : 
                    `${percentage}% a ${days} días`;
            }
        });

        return descriptions.join(", ");
    }

    // Verificar si se puede confirmar
    canConfirm() {
        // !! convierte el valor a un booleano (true si hay un objeto, false si es null/undefined)
        const termIsSelected = !!this.state.selectedPaymentTerm;
    
        console.log("--- Evaluando canConfirm() ---");
        console.log("¿Hay un término seleccionado?:", termIsSelected);
        // Ahora usamos el nombre correcto de la propiedad
        console.log("Valor de state.selectedPaymentTerm:", this.state.selectedPaymentTerm);
        console.log("------------------------------");
    
        return termIsSelected;
    }
    // Confirmar selección
    async confirm() {
        console.log("Entra en el confirm");
        if (!this.canConfirm()) {
            return;
        }
        super.confirm();
    }
}