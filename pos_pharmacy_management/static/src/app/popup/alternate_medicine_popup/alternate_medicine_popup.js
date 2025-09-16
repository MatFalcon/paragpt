/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AlternateMedicinePopup extends AbstractAwaitablePopup {
    static template = "pos_pharmacy_management.AlternateMedicinePopup";
    static components = { ProductCard };

    setup() {
        super.setup();
        this.pos = usePos();
        this.popup = useService("popup");
        onMounted(this.onMounted);
    }
    onMounted(){
        $('#alternate_med_popup .product').on('click', function(ev) {
            $(ev.currentTarget).toggleClass('selected');
        });
    }
    confirm(ev){
        var self = this;
        var records = $('article.product.selected');
        var order = this.pos.get_order();
        if(order && records.length){
            $.each(records, function(key, record) {
                var prod_id = record.getAttribute('data-product-id');
                var product = self.pos.db.get_product_by_id(prod_id);
                if(product) order.add_product(product);
            });
        }
        self.cancel();
    }
    get_string(key, ids){
        var self = this;
        var str = "";
        var data;
        if(key === 'product'){
            data = self.pos.db.product_by_id;
            ids.forEach(id => {
                str += `${data[id].display_name}, `;
            });
        }
        else{
            if(key === 'medicine_salt') data = self.pos.medicine_salt;
            else if(key === 'medicine_usage') data = self.pos.medicine_usage;
            else if(key === 'salt_composition') data = self.pos.salt_composition;
            else if(key === 'side_effects') data = self.pos.side_effects;
            else if(key === 'safety_advice') data = self.pos.safety_advice;
            else if(key === 'basic_salt') data = self.pos.basic_salt;
            ids.forEach(id => {
                if(data && data[id - 1]) str += `${data[id].name}, `;
            });
        }
        if(str.length >35){
            str = str.slice(0, 35);
            str += "....."; 
            return str;
        }
        return str;
    }
    async onSaltBasedProductsClick(product) {
        var list = this.pos.db.get_product_by_category(this.pos.selectedCategoryId);
        var med_ids = [];
        list.forEach(prod => {
            prod.salt_composition_ids.forEach(id => {
                if(product.salt_composition_ids.includes(id)){
                    med_ids.push(prod.id);
                    return false;
                }
            });
        });
        med_ids = [...new Set(med_ids)];
        this.popup.add(AlternateMedicinePopup, {product : product, med_ids : med_ids});
    }
}
