/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { PosDB } from "@point_of_sale/app/store/db";

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this._loadmedicinemanufacturer(loadedData["medicine.manufacturer"]);
        this._loadbasicsalt(loadedData["basic.salt"]);
        this._loadsaltunit(loadedData["salt.unit"]);
        this._loadmedicinesalt(loadedData["medicine.salt"]);
        this._loadsaltcomposition(loadedData["salt.composition"]);
        this._loadmedicineusage(loadedData["medicine.usage"]);
        this._loadsideeffects(loadedData["side.effects"]);
        this._loadsafetyadvice(loadedData["safety.advice"]);
        this._loadchemicalclass(loadedData["chemical.class"]);
        this._loadtherapeuticclass(loadedData["therapeutic.class"]);
        this._loadactionclass(loadedData["action.class"]);
        this._loadfactbox(loadedData["fact.box"]);
        this._loadproductuomprice(loadedData["product.uom.price"]);
        this._loaduomuom(loadedData["uom.uom"]);
        this._loaduomcategory(loadedData["uom.category"]);
        this.numero_matricula
    },
    _loadmedicinemanufacturer(result) {
        this.medicine_manufacturer = {};
        result.forEach(data => {
            this.medicine_manufacturer[data.id] = data;
        });
    },
    _loadbasicsalt(result) {
        this.basic_salt = {};
        result.forEach(data => {
            this.basic_salt[data.id] = data;
        });
    },
    _loadsaltunit(result) {
        this.salt_unit = {};
        result.forEach(data => {
            this.salt_unit[data.id] = data;
        });
    },
    _loadmedicinesalt(result) {
        this.medicine_salt = {};
        result.forEach(data => {
            this.medicine_salt[data.id] = data;
        });
    },
    _loadsaltcomposition(result) {
        this.salt_composition = {};
        result.forEach(data => {
            this.salt_composition[data.id] = data;
        });
    },
    _loadmedicineusage(result) {
        this.medicine_usage = {};
        result.forEach(data => {
            this.medicine_usage[data.id] = data;
        });
    },
    _loadsideeffects(result) {
        this.side_effects = {};
        result.forEach(data => {
            this.side_effects[data.id] = data;
        });
    },
    _loadsafetyadvice(result) {
        this.safety_advice = {};
        result.forEach(data => {
            this.safety_advice[data.id] = data;
        });
    },
    _loadchemicalclass(result) {
        this.chemical_class = {};
        result.forEach(data => {
            this.chemical_class[data.id] = data
        });
    },
    _loadtherapeuticclass(result) {
        this.therapeutic_class = {};
        result.forEach(data => {
            this.therapeutic_class[data.id] = data
        });
    },
    _loadactionclass(result) {
        this.action_class = {};
        result.forEach(data => {
            this.action_class[data.id] = data
        });
    },
    _loadfactbox(result) {
        this.fact_box = {};
        result.forEach(data => {
            this.fact_box[data.id] = data
        });
    },
    _loadproductuomprice(result) {
        this.product_uom_price = {};
        result.forEach(data => {
            this.product_uom_price[data.id] = data
        });
    },
    _loaduomcategory(result) {
        this.uom_categories = {};
        result.forEach(data => {
            this.uom_categories[data.id] = data
        });
    },
    async getProductStocks(product_id){
        let stocks = await this.env.services.orm.silent.call(
            'pos.session',
            'getStocks',
            [[], this.config.id, product_id],
        );
        return stocks
    },
    _loaduomuom(result) {},
    async selectDoctor(){
        const currentOrder = this.get_order();
        if (!currentOrder) return;
        const currentDoctor = currentOrder.get_doctor();
        if (currentDoctor && currentOrder.getHasRefundLines()) {
            this.popup.add(ErrorPopup, {
                title: _t("Can't change Doctor"),
                body: _t("This order already has refund lines for %s. We can't change the customer associated to it. Create a new order for the new customer.", currentDoctor.name),
            });
            return;
        }
        const { confirmed, payload: newDoctor } = await this.showTempScreen("PartnerListScreen", {
            partner: currentDoctor, 
            doctor : true,
        });
        if (confirmed) {
            currentOrder.set_doctor(newDoctor);
        }
    },
    onClickHidePads(){
        $('.subpads').removeClass('d-flex');
        $('.subpads').hide();
        $('.show-pads').css({'display' : 'flex'});
    },
    onClickShowPads(){
        $('.subpads').addClass('d-flex');
        $('.show-pads').hide();
    },
    async change_view(){
        let view = this.config.product_display_type;
        view === 'grid' ? this.config.product_display_type = 'list' : this.config.product_display_type = 'grid';
        if(this.config.product_display_type === 'list'){
            $('.product-list').removeClass('d-grid');
            $('.product-list').addClass('d-flex');
            $('.product-list').css('flex-direction', 'column');
        }else{
            $('.product-list').removeClass('d-flex');
            $('.product-list').addClass('d-grid');
        }
    },
    getReceiptHeaderData(order) {
        const result = super.getReceiptHeaderData(...arguments);
        if (this.get_order() && this.get_order().doctor) {
            result.doctor = this.get_order().doctor;
        }
        return result;
    },
});

patch(PosDB.prototype, {
    _partner_search_string(partner) {
        var str = super._partner_search_string(partner);
        if (partner.ref) {
            str = str.substr(0, str.length - 1) + "|" + partner.numero_matricula + "\n";
        }
        console.log('lista de string', str)
        return str;
    },
});