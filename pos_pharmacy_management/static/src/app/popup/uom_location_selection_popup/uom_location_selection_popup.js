/** @odoo-module **/
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
import { _t } from '@web/core/l10n/translation';

export class UomLocationSelectionPopup extends AbstractAwaitablePopup {
    static template = "pos_pharmacy_management.UomLocationSelectionPopup";
    static props = {
        title: String,
        product: Object,
        initialQuantity: { type: Number, optional: true },
        closeAll: { type: Boolean, optional: true },
        '*': { type: Object, optional: true },
    };

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.pos = useService("pos");
        this.state = useState({
            step: 'uom', // 'uom', 'location', 'lot', 'assignment'
            // UoM step
            selectedUomLine: null,
            quantity: this.props.initialQuantity || 1,
            // Location step
            locations: [],
            selectedLocation: null,
            // Lot step
            lots: [],
            selectedLots: [],
            assignmentProposal: null,
            loading: false,
            baseQuantityNeeded: this.props.initialQuantity || 1
        });
    }

    // ===== UoM SELECTION METHODS =====
    selectUomLine(uomLine) {
        this.state.selectedUomLine = uomLine;
        
        // Recalcular cantidad base necesaria
        this.state.baseQuantityNeeded = this.state.quantity * uomLine.qty;
    }

    updateQuantity(newQty) {
        this.state.quantity = Math.max(1, newQty);
        if (this.state.selectedUomLine) {
            this.state.baseQuantityNeeded = this.state.quantity * this.state.selectedUomLine.qty;
        }
    }

    async proceedToLocationSelection() {
        if (!this.state.selectedUomLine) {
            return;
        }
        
        // Si el producto no requiere tracking, confirmar directamente
        if (this.props.product.tracking === 'none') {
            this.props.close({
                confirmed: true,
                payload: {
                    uomLine: this.state.selectedUomLine,
                    quantity: this.state.quantity
                }
            });
            return;
        }
        
        // Cargar ubicaciones disponibles
        this.state.loading = true;
        try {
            const locations = await this.orm.call(
                "pos.session",
                "get_available_locations_for_pos_product",
                [],
                { product_id: this.props.product.id }
            );
            this.state.locations = locations;
            this.state.step = 'location';
        } catch (error) {
            console.error("Error loading locations:", error);
        }
        this.state.loading = false;
    }

    // ===== LOCATION SELECTION METHODS =====
    async selectLocation(location) {
        this.state.selectedLocation = location;
        this.state.loading = true;
        
        try {
            const lots = await this.orm.call(
                "pos.session",
                "get_lots_by_location",
                [],
                {
                    product_id: this.props.product.id,
                    location_id: location.id
                }
            );
            this.state.lots = lots;
            this.state.step = 'lot';
        } catch (error) {
            console.error("Error loading lots:", error);
        }
        this.state.loading = false;
    }

    // ===== LOT SELECTION METHODS =====
    toggleLotSelection(lot) {
        const index = this.state.selectedLots.findIndex(l => l.id === lot.id);
        if (index > -1) {
            this.state.selectedLots.splice(index, 1);
        } else {
            this.state.selectedLots.push({
                ...lot,
                qtyToUse: Math.min(lot.available_qty, this.state.baseQuantityNeeded)
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
                    requested_qty: this.state.baseQuantityNeeded,
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

    // ===== CONFIRMATION METHODS =====
    confirmManualSelection() {
        const totalQty = this.getTotalSelectedQty();
        if (totalQty <= 0) {
            return;
        }

        this.props.close({
            confirmed: true,
            payload: {
                uomLine: this.state.selectedUomLine,
                quantity: this.state.quantity,
                type: 'manual',
                selectedLots: this.state.selectedLots,
                location: this.state.selectedLocation,
                totalQty: totalQty
            }
        });
    }

    acceptProposal() {
        if (this.state.assignmentProposal) {
            this.props.close({
                confirmed: true,
                payload: {
                    uomLine: this.state.selectedUomLine,
                    quantity: this.state.quantity,
                    type: 'proposal',
                    assignment: this.state.assignmentProposal.assignment,
                    location: this.state.selectedLocation
                }
            });
        }
    }

    // ===== NAVIGATION METHODS =====
    goBack() {
        if (this.state.step === 'location') {
            this.state.step = 'uom';
            this.state.locations = [];
        } else if (this.state.step === 'lot') {
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