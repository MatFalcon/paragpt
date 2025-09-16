/** @odoo-module **/

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { MedicineProductInfoPopup } from "@pos_pharmacy_management/app/popup/medicine_product_info_popup/medicine_product_info_popup";
import { AlternateMedicinePopup } from "@pos_pharmacy_management/app/popup/alternate_medicine_popup/alternate_medicine_popup";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";

export class WkProductCard extends Component {
    static template = "pos_pharmacy_management.WkProductCard";
    static props = {
        class: { String, optional: true },
        name: String,
        productId: Number,
        price: String,
        imageUrl: String,
        onClick: { type: Function, optional: true },
    };
    static defaultProps = {
        onClick: () => {},
        class: "",
    };
    
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.popup = useService("popup");
        onMounted(this.onMounted);
    }
    onMounted() {
        $('.pos .product').on('dragstart', function (event) {
            event.originalEvent.dataTransfer.clearData();
            event.originalEvent.dataTransfer.setData("text", event.currentTarget.dataset.productId);
        });
    }
    async onMedProductInfoClick(product) {
        const info = await this.pos.getProductInfo(product, 1);
        var stocks = await this.pos.getProductStocks(product.id);
        if(stocks) product.stocks = stocks;
        this.popup.add(MedicineProductInfoPopup, { info: info , product: product });
    }
    async onAlternateMedicineClick(product) {
        this.popup.add(AlternateMedicinePopup, {product : product, med_ids : product.medicine_substitute_ids});
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
    get_string(key, ids){
        var self = this;
        var str = '';
        var products = self.pos.db.product_by_id;

        if(key === 'product'){
            ids.forEach(id => { if(products[id]) str += `${products[id].display_name}, ` });
        }
        else{
            if(key === 'medicine_salt') products = self.pos.medicine_salt;
            else if(key === 'medicine_usage') products = self.pos.medicine_usage;
            else if(key === 'salt_composition') products = self.pos.salt_composition;
            else if(key === 'side_effects') products = self.pos.side_effects;
            else if(key === 'safety_advice') products = self.pos.safety_advice;
            else if(key === 'basic_salt') products = self.pos.basic_salt;
            ids.forEach(id => { if(products[id]){
                if(products && products[id - 1]) str += `${products[id].name}, `;
            } });
        }
        if(str.length >35){
            str = str.slice(0, 35);
            str += "....."; 
            return str;
        }
        return str;
    }
}
