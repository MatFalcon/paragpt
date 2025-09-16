/** @odoo-module **/

import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { AdvanceMedicineSearchPopup } from "@pos_pharmacy_management/app/popup/advance_medicine_search_popup/AdvanceMedicineSearchPopup";

export class AdvanceSearchButton extends Component {
    static template = "pos_pharmacy_management.AdvanceSearchButton";
    
    setup() {
        this.pos = usePos();
        this.popup = useService("popup");
    }
    async onClick() {
        await this.popup.add(AdvanceMedicineSearchPopup, {
            title: "Advance Search(Medicine)",
            cancelText: "Cancel",
        });
    }
}

ProductScreen.addControlButton({
    component: AdvanceSearchButton,
    condition: function () {
        return this.pos.config.advance_search && this.pos.config.icon_display_type == 'control_button';
    },
});