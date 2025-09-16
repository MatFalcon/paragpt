/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { onMounted } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";
import { UomLocationSelectionPopup } from "@pos_pharmacy_management/app/popup/uom_location_selection_popup/uom_location_selection_popup";

export class ShowUomOptionsPopup extends AbstractAwaitablePopup {
    static template = "pos_pharmacy_management.ShowUomOptionsPopup";
    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(this.onMounted);
    }
    
    onMounted() {
        var self = this;
        var line = self.pos.get_order().selected_orderline;
        const $qtyInput = $('#qtyInput');
        const $message = $('#message');
        
        if (line.uom_line && line.uom_line.id) {
            $(`div.uom_line[uom-id=${line.uom_line.id}]`).addClass("active_uom");
            $(".qty_input").val(1);
        }
        else {
            $('div.uom_line').removeClass("active_uom");
            $(".qty_input").val(1);
        }
        
        $qtyInput.on('blur', function () {
            if ($qtyInput.val() === '' || $qtyInput.val() == 0) {
                $message.show();
                $qtyInput.css("border", "2px solid red")
            } else {
                $message.hide();
            }
        });

        $qtyInput.on('focus', function () {
            $message.hide();
            $qtyInput.css("border", "2px solid #017e84")
        });
    }
    
    async onShowUomClick(event, uom_id) {
        var uom_line = this.pos.product_uom_price[uom_id];
        this.pos.get_order().selected_orderline['uom_line'] = uom_line;
        $(event.srcElement).parents('.uom_popup_body').find(`.active_uom`).removeClass("active_uom");
        $(event.srcElement).parents(`.uom_line[uom-id=${uom_id}]`).addClass("active_uom");
    }
    
    async onShowpreviousUom(event, uom_id) {
        var uom_line = this.pos.units_by_id[uom_id];
        this.pos.get_order().selected_orderline['uom_line'] = uom_line;
        $(event.srcElement.offsetParent).find(`.active_uom`).removeClass("active_uom");
        $(event.srcElement.offsetParent).find(`.previous_uom_line[previous-uom-id=${uom_id}]`).addClass("active_uom");
    }
    
    async confirm(){
        var self = this;
        var line = self.pos.get_order().selected_orderline;
        var uom_line = line ? line.uom_line : null;
        var qty_entered = parseFloat($(".qty_input").val()) || 1;
        
        if (line && uom_line) {
            if (line.product.uom_po_id !== undefined && line.uom_line.id === line.product.uom_po_id[0]) {
                // Unidad de compra estándar
                line.product.uom_id = line.product.uom_po_id
                line.set_unit(line.product.uom_po_id[0]);
                var price = line.product.get_price(self.pos.get_order().pricelist, qty_entered, line.get_price_extra())
                line.set_quantity(qty_entered);
                line.set_unit_price(price);
            }
            else {
                // UOM personalizado de farmacia
                if (qty_entered > 0) {
                    line.product.uom_id = uom_line.uom_id;
                    line.set_unit(uom_line.uom_id[0]);
                    line.set_quantity(qty_entered);
                    line.set_unit_price(uom_line.unit_price);
                    line.price_type = "manual";
                    line.uom_line = uom_line;
                    line.secondary_uom_id = uom_line.uom_id[0];
                    
                    // YA NO necesitamos seleccionar ubicación/lotes aquí
                    // porque ya se hizo en getAddProductOptions()
                } else {
                    self.set_line_unit(uom_line);
                }
            }
        }
        this.cancel();
    }
    
    set_line_unit(uom_line) {
        var self = this;
        var line = self.pos.get_order().selected_orderline;
        line.set_unit(uom_line.uom_id[0]);
        line.product.uom_id = uom_line.uom_id;
        line.set_unit_price(uom_line.unit_price);
        line.set_quantity(1);
        line.price_type = "manual";
        line.uom_line = uom_line;
        line.secondary_uom_id = uom_line.uom_id[0];
    }
}

// MODIFICAR EL PATCH DE ProductScreen para que NO llame al popup de UoM
// si ya se procesó en getAddProductOptions
patch(ProductScreen.prototype, {
    async _setValue(val) {
        var self = this;
        var line = self.env.pos.get_order().get_selected_orderline();
        
        if (line.refunded_orderline_id) {
            this.popup.add(ErrorPopup, {
                title: 'Quantity not changed',
                body: "You cannot make changes to the quantity of the orderline as it's and return order.",
            });
        }
        else {
            if (self.env.pos.numpadMode === 'quantity') {
                if (val == "") {
                    NumberBuffer.reset();
                    self.env.pos.get_order().remove_orderline(line);
                    return
                }
                else {
                    // Solo mostrar popup de UoM si estamos MODIFICANDO una línea existente
                    // y no cuando se está agregando el producto por primera vez
                    if (line !== undefined && 
                        line.product.product_price_by_uom.length && 
                        line.product.manage_multi_uom_via_price &&
                        line.id // Verificar que la línea ya existe (no es nueva)
                    ) {
                        var selected_orderline = line
                        this.popup.add(ShowUomOptionsPopup, {
                            title: 'Medicine Units',
                            line: line,
                            selected_uom_id: selected_orderline.uom_id,
                            previous_unit: line.product.uom_id
                        });
                    }
                    else {
                        return super._setValue(...arguments)
                    }
                }
            }
            else {
                return super._setValue(...arguments)
            }
        }
    }
});