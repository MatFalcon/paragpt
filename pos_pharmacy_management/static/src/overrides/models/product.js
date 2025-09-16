/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Order } from "@point_of_sale/app/store/models";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { Product } from "@point_of_sale/app/store/models";
import { jsonrpc } from "@web/core/network/rpc_service";
import { ComboConfiguratorPopup } from "@point_of_sale/app/store/combo_configurator_popup/combo_configurator_popup";
import { _t } from '@web/core/l10n/translation';
import { EditListInput } from "@point_of_sale/app/store/select_lot_popup/edit_list_input/edit_list_input";
import {EditListPopup} from "@point_of_sale/app/store/select_lot_popup/select_lot_popup";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { LocationLotSelectionPopup } from "@pos_pharmacy_management/app/popup/location_lot_selection_popup/location_lot_selection_popup";
import { UomLocationSelectionPopup } from "@pos_pharmacy_management/app/popup/uom_location_selection_popup/uom_location_selection_popup";
import {useState} from "@odoo/owl";
import { ShowUomOptionsPopup } from "@pos_pharmacy_management/app/popup/show_uom_options_popup/show_uom_options_popup";

const PosService = {
    getInstance() {
        return window.pos || 
               window.odoo.__WOWL_DEBUG__.root.env.services.pos ||
               window.PointOfSale;
    }
};

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
                { product: this, keepBehind: true }
            );
            if (!confirmed) {
                return;
            }
            comboLines = payload;
        }

        //Para abrir el popup de multi unidad de medida original del modulo
        // if (this.product_price_by_uom.length && this.manage_multi_uom_via_price) {
        //     console.log("ES MULTI MEDIDA DEBE DE ENTRAR ACA");
        //     const { confirmed, payload } = await this.env.services.popup.add(
        //         ShowUomOptionsPopup,
        //         {
        //             title: 'Seleccionar Unidad de Medida',
        //             product: this,
        //             initialQuantity: quantity
        //         }
        //     );
        //     console.log("SE SELECCIONO LA MULTIMEDIDA");
            
        //     if (!confirmed) {
        //         return;
        //     }
            
        //     selectedUomLine = payload.uomLine;
        //     quantity = payload.quantity;
            
        //     // Actualizar precio basado en UoM seleccionada
        //     if (selectedUomLine) {
        //         price_extra += selectedUomLine.unit_price - this.get_price(this.pos.get_order().pricelist, 1);
        //     }
        // }


        //forma 2 para unificar la seleccion de multimedida y ubicaciones/lotes


        // USAR EL NUEVO POPUP COMBINADO si tiene multi-UoM O requiere tracking
        if ((this.product_price_by_uom.length && this.manage_multi_uom_via_price) || this.isTracked()) {
            const { confirmed, payload } = await this.env.services.popup.add(
                UomLocationSelectionPopup,
                {
                    title: 'Configurar Producto',
                    product: this,
                    initialQuantity: quantity
                }
            );
            
            if (!confirmed) {
                return;
            }
            
            // Actualizar valores basados en la selección
            quantity = payload.quantity;
            
            if (payload.uomLine) {
                price_extra += payload.uomLine.unit_price - this.get_price(this.pos.get_order().pricelist, 1);
            }
            
            // Procesar lotes si fueron seleccionados
            if (payload.selectedLots || payload.assignment) {
                let selectedLots = [];
                if (payload.type === 'manual') {
                    selectedLots = payload.selectedLots;
                } else if (payload.type === 'proposal') {
                    selectedLots = payload.assignment.map(assign => ({
                        name: assign.lot_name,
                        qtyToUse: assign.qty_assigned
                    }));
                }
                
                if (selectedLots.length > 0) {
                    const newPackLotLines = selectedLots.map(lot => ({
                        lot_name: lot.name,
                        quantity: lot.qtyToUse
                    }));
                    
                    draftPackLotLines = { 
                        modifiedPackLotLines: {}, 
                        newPackLotLines: newPackLotLines 
                    };
                }
            }
            
            // Guardar información de UoM para la línea de pedido
            if (payload.uomLine) {
                this._selectedUomLine = payload.uomLine;
            }
        }

    // Take the weight if necessary.
    if (this.to_weight && this.pos.config.iface_electronic_scale) {
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
        selectedUomLine: this._selectedUomLine, // Información de UoM para usar en la línea
    };
}
});

patch(EditListInput.prototype, {
    setup() {
        this._super && this._super(...arguments);
        this.listaLotes = this.listaLotes.bind(this);
        this.popup = useService("popup");
        this.state = useState({ text: this.props.item.text });
    },

    async listaLotes() {
        const pos = PosService.getInstance();
        const order = pos.get_order();
        const orderline = pos.get_order()?.selected_orderline;
        if (!pos?.db) {
            throw new Error("No se puede acceder a la base de datos del POS");
        }
        const product = pos.get_order()?.selected_orderline?.product;

        const result = await this.env.services.orm.call(
            "stock.lot", 
            "get_available_lots_for_pos",
            [], 
            {
                product_id: product.id,
                valor: 2
            }
        );
        const popup = await this.env.services.popup.add(LotSelectionPopup, {
            title: 'Seleccionar Lote',
            lots: result,
        });
        
        if (popup.confirmed && popup.payload) {
            if (orderline) {
                orderline.setPackLotLines({
                    modifiedPackLotLines: {lot_name: popup.payload},
                    newPackLotLines: [{ lot_name: popup.payload }]
                });
                console.log('item', this.props.item);
            }
            const selectedLot = popup.payload;
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    if (mutation.type === 'childList') {
                        const popupParent = document.querySelector('.popup, .o_popup, [class*="popup"]');
                        if (!popupParent) {
                            if (orderline) {
                                orderline.setPackLotLines({
                                    modifiedPackLotLines: {lot_name: selectedLot},
                                    newPackLotLines: [{ lot_name: selectedLot }]
                                });
                            }
                            observer.disconnect();
                        }
                    }
                });
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            setTimeout(() => {
                const popups = document.querySelectorAll('.popup, .o_popup, [class*="popup"]');
                for (let popup of popups) {
                    const confirmButton = popup.querySelector('.btn-primary') || 
                                        popup.querySelector('.btn-success') ||
                                        popup.querySelector('[data-action="confirm"]') ||
                                        popup.querySelector('button[class*="primary"]');
                    
                    if (confirmButton) {
                        setTimeout(() => {
                            confirmButton.click();
                        }, 100);
                        return;
                    }
                }
            }, 100);
        }
    },
});

patch(Order.prototype, {
    async pay() {
        if (!this.canPay()) {
            return;
        }
        if (
            this.orderlines.some(
                (line) => line.get_product().tracking !== "none" && !line.has_valid_product_lot()
            ) &&
            (this.pos.picking_type.use_create_lots || this.pos.picking_type.use_existing_lots)
        ) {
            const { confirmed } = await this.env.services.popup.add(ConfirmPopup, {
                title: _t("Some Serial/Lot Numbers are missing"),
                body: _t(
                    "No se puede realizar la venta, ya que hay productos sin lote seleccionado. \nPor favor, seleccione el lote y vuelva a intentar."
                ),
            });
        } else {
            this.pos.mobile_pane = "right";
            this.env.services.pos.showScreen("PaymentScreen");
        }
    }
});

export class LotSelectionPopup extends AbstractAwaitablePopup {     
    static template = "pos_auto_lot_selection.LotSelectionPopup";
    static props = {
        title: String,
        lots: Array,
        closeAll: { type: Boolean, optional: true },
        '*': { type: Object, optional: true },
    };
    setup() {
        this.state = useState({ selectedLot: null });
        console.log("lotes:", this.props.lots);
    }
    confirmSelection() {
        if (this.state.selectedLot) {
            this.props.close({ confirmed: true, payload: this.state.selectedLot});
        }
    }
}