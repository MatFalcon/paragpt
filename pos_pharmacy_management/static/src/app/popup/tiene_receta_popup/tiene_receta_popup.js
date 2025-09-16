/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { Order, Orderline } from "@point_of_sale/app/store/models";
import { Product } from "@point_of_sale/app/store/models";
import {useState} from "@odoo/owl";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";

patch(Product.prototype, {
    async getAddProductOptions(code) {
        let price_extra = 0.0;
        let draftPackLotLines, packLotLinesToEdit, attribute_value_ids;
        let quantity = 1;
        let comboLines = [];
        let attribute_custom_values = {};

        if (code && this.pos.db.product_packaging_by_barcode[code.code]) {
            quantity = this.pos.db.product_packaging_by_barcode[code.code].qty;
        }

        if (this.isConfigurable()) {
            const { confirmed, payload } = await this.openConfigurator({ initQuantity: quantity });
            if (confirmed) {
                attribute_value_ids = payload.attribute_value_ids;
                attribute_custom_values = payload.attribute_custom_values;
                price_extra += payload.price_extra;
                quantity = payload.quantity;
            } else {
                return;
            }
        }
        if (this.combo_ids.length) {
            const { confirmed, payload } = await this.env.services.popup.add(
                ComboConfiguratorPopup,
                { product: this }
            );
            if (!confirmed) {
                return;
            }
            comboLines = payload;
        }
        // Gather lot information if required.
        if (this.isTracked()) {
            packLotLinesToEdit =
                (!this.isAllowOnlyOneLot() &&
                    this.pos.selectedOrder
                        .get_orderlines()
                        .filter((line) => !line.get_discount())
                        .find((line) => line.product.id === this.id)
                        ?.getPackLotLinesToEdit()) ||
                [];
            // if the lot information exists in the barcode, we don't need to ask it from the user.
            if (this.is_prescription == true)
            {
                const doctorPartner = await this.env.services.orm.searchRead(
                    'res.partner',
                    [['is_a_doctor', '=', true]],
                    ['name', 'email', 'phone', 'mobile', 'numero_matricula'],
                    { limit: 1000 }
                );
                console.log("partners encontrados", doctorPartner)
                const {confirmed, datos} = await this.env.services.popup.add(PrescriptionPopup,{
                    title: _t("Producto Controlado"),
                    name: this.name,
                    doctor: doctorPartner
                });
                if (confirmed == true)
                {
                    return datos
                }
            }
            if (code && code.type === "lot") {
                // consider the old and new packlot lines
                const modifiedPackLotLines = Object.fromEntries(
                    packLotLinesToEdit.filter((item) => item.id).map((item) => [item.id, item.text])
                );
                const newPackLotLines = [{ lot_name: code.code }];
                draftPackLotLines = { modifiedPackLotLines, newPackLotLines };
            }
            if (!draftPackLotLines) {
                return;
            }
        }

        // Take the weight if necessary.
        if (this.to_weight && this.pos.config.iface_electronic_scale) {
            // Show the ScaleScreen to weigh the product.
            if (this.isScaleAvailable) {
                const product = this;
                const { confirmed, payload } = await this.env.services.pos.showTempScreen(
                    "ScaleScreen",
                    {
                        product,
                    }
                );
                if (confirmed) {
                    quantity = payload.weight;
                } else {
                    // do not add the product;
                    return;
                }
            } else {
                await this._onScaleNotAvailable();
            }
        }

        return {
            draftPackLotLines,
            quantity,
            attribute_custom_values,
            price_extra,
            comboLines,
            attribute_value_ids,
        };
    }
});

export class PrescriptionPopup extends AbstractAwaitablePopup {
    static template = 'pos_pharmacy_management.IsPrescription';
    static props = {
        name: String,
        doctor: Array
    };
    setup() {
        this.state = useState({
            name: "",
            selectedDoctorId: ""
        });
    };

    confirmSelection(){
        console.log("matricula", this.state.selectedDoctorId)
        if (this.state.selectedDoctorId)
        {
            this.props.close({
                confirmed: true, 
                datos: this.state.selectedDoctorId
            })
        }
    };
};
