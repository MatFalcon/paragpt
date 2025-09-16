/** @odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { _t } from '@web/core/l10n/translation';

export class LocationLotSelectionPopup extends AbstractAwaitablePopup {
    static template = "pos_pharmacy_management.LocationLotSelectionPopup";
    static props = {
        title: String,
        product: Object,
        requestedQty: Number,
        uomLine: { type: Object, optional: true },
        closeAll: { type: Boolean, optional: true },
        '*': { type: Object, optional: true },
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = useState({
            step: 'location', // 'location', 'lot', 'assignment'
            locations: [],
            selectedLocation: null,
            lots: [],
            selectedLots: [],
            assignmentProposal: null,
            loading: false
        });
        
        this.loadAvailableLocations();
    }

    async loadAvailableLocations() {
        console.log("ENTRA EN loadAvailableLocations")
        this.state.loading = true;
        try {
            console.log("LLAMAMOS A LA FUNCION DE POS SESSION")
            console.log("VAMOS A BUSCAR EL PRODUCTO", this.props.product.id)
            const  locations = await this.env.services.orm.call(
                "pos.session",
                "get_available_locations_for_pos_product",
                [],
                { product_id: this.props.product.id }
            );
            console.log("SE LLAMO A LA FUNCION")
            this.state.locations = locations;
            console.log("LAS UBICACIONES SON");
            console.log(this.state.locations);
        } catch (error) {
            console.error("Error loading locations:", error);
        }
        this.state.loading = false;
        console.log("SE PUSO EN FALSE?");
    }

    async selectLocation(location) {
        console.log("ENTRA EN LA FUNCION selectLocation");
        this.state.selectedLocation = location;
        this.state.loading = true;
        console.log("PAso 2")
        
        try {
            const lots = await this.env.services.orm.call(
                "pos.session",
                "get_lots_by_location",
                [],
                {
                    product_id: this.props.product.id,
                    location_id: location.id
                }
            );
            console.log("LOTES", lots);
            this.state.lots = lots;
            this.state.step = 'lot';
        } catch (error) {
            console.error("Error loading lots:", error);
        }
        this.state.loading = false;
    }

    toggleLotSelection(lot) {
        console.log("ENTRA EN toggleLotSelection");
        const index = this.state.selectedLots.findIndex(l => l.id === lot.id);
        console.log("INDICE", index)
        if (index > -1) {
            this.state.selectedLots.splice(index, 1);
        } else {
            this.state.selectedLots.push({
                ...lot,
                qtyToUse: Math.min(lot.available_qty, this.props.requestedQty)
            });
        }
    }

    isLotSelected(lot) {
        return this.state.selectedLots.some(l => l.id === lot.id);
    }

    updateLotQuantity(lotId, newQty) {
        const lot = this.state.selectedLots.find(l => l.id === lotId);
        if (lot) {
            lot.qtyToUse = Math.max(0, Math.min(newQty, lot.available_qty));
        }
    }

    getTotalSelectedQty() {
        return this.state.selectedLots.reduce((sum, lot) => sum + lot.qtyToUse, 0);
    }

    async getAutomaticProposal() {
        this.state.loading = true;
        
        try {
            const proposal = await this.orm.call(
                "pos.session",
                "get_lot_assignment_proposal",
                [],
                {
                    product_id: this.props.product.id,
                    requested_qty: this.props.requestedQty,
                    preferred_locations: this.state.selectedLocation ? [this.state.selectedLocation.id] : null
                }
            );
            
            this.state.assignmentProposal = proposal;
            this.state.step = 'assignment';
        } catch (error) {
            console.error("Error getting automatic proposal:", error);
        }
        this.state.loading = false;
    }

    acceptProposal() {
        if (this.state.assignmentProposal) {
            this.props.close({
                confirmed: true,
                payload: {
                    type: 'proposal',
                    assignment: this.state.assignmentProposal.assignment,
                    location: this.state.selectedLocation
                }
            });
        }
    }

    confirmManualSelection() {
        const totalQty = this.getTotalSelectedQty();
        if (totalQty <= 0) {
            return; // No se puede confirmar sin selección
        }

        this.props.close({
            confirmed: true,
            payload: {
                type: 'manual',
                selectedLots: this.state.selectedLots,
                location: this.state.selectedLocation,
                totalQty: totalQty
            }
        });
    }

    goBack() {
        if (this.state.step === 'lot') {
            this.state.step = 'location';
            this.state.selectedLocation = null;
            this.state.lots = [];
        } else if (this.state.step === 'assignment') {
            this.state.step = 'lot';
            this.state.assignmentProposal = null;
        }
    }

    cancel() {
        this.props.close({ confirmed: false });
    }
}