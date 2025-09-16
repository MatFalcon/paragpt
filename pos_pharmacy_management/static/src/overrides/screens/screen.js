/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { CategorySelector } from "@point_of_sale/app/generic_components/category_selector/category_selector";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { ConfirmPopup } from "@point_of_sale/app/utils/confirm_popup/confirm_popup";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { PartnerListScreen } from "@point_of_sale/app/screens/partner_list/partner_list";
import { PrescriptionConfirmPopup } from "@pos_pharmacy_management/app/popup/prescription_confirm_popup/prescription_confirm_popup";
import { MedicineProductInfoPopup } from "@pos_pharmacy_management/app/popup/medicine_product_info_popup/medicine_product_info_popup";
import { AdvanceMedicineSearchPopup } from "@pos_pharmacy_management/app/popup/advance_medicine_search_popup/AdvanceMedicineSearchPopup";
import { WkProductCard } from "@pos_pharmacy_management/app/components/wk_product_card/wk_product_card";
import { ShowUomOptionsPopup } from "@pos_pharmacy_management/app/popup/show_uom_options_popup/show_uom_options_popup";
import { registry } from "@web/core/registry";
import { onMounted } from "@odoo/owl";

registry.category("pos_models").add("res.partner", {
    fields: {
        numero_matricula: { type: "string" },
    },
});

patch(Orderline.prototype, {
    async onMedProductInfoClick(){
        const product = this.props.line.product;
        const info = await this.env.services.pos.getProductInfo(product, 1);
        var stocks = await this.env.services.pos.getProductStocks(product.id);
        if(stocks) product.stocks = stocks;
        this.env.services.popup.add(MedicineProductInfoPopup, { info: info , product: product });
    },
    onShowUomClick(line) {
        if (line.product.product_price_by_uom.length) {
            var selected_orderline = this.env.services.pos.get_order().get_selected_orderline()
            this.env.services.popup.add(ShowUomOptionsPopup, {
                title: 'Medicine Units',
                line: line,
                selected_uom_id: selected_orderline.uom_id,
                previous_unit: selected_orderline.product.uom_po_id
            });
        }
    },
    onClickDeleteLine(){
        let currentOrder = this.env.services.pos.get_order();
        currentOrder.removeOrderline(currentOrder.get_orderline(this.props.line.id));
    },
    uom_category_is_medicine(){
        let categ_id, is_med;
        var uom_id = this.props.line.product.uom_id[0];

        this.env.services.pos.units.forEach(unit => {
            if(unit.id === uom_id) categ_id = unit.category_id[0];
        });

        if(categ_id){
            Object.values(this.env.services.pos.uom_categories).forEach(uom_categ => {
                if(uom_categ.id === categ_id && uom_categ.is_medicine) is_med = true;
            });
        }
        return is_med;
    },
});
patch(ProductScreen.prototype,{
    onMounted() {
        super.onMounted();
        var self = this;
        self.pos.config.icon_display_type == 'icon' ? self.pos.show_bar = false : self.pos.show_bar = true;
        if(self.pos.config.configurable_color && self.pos.config.config_color){
            var styles = `
                .pos .pos-topheader{
                    background-color : ${self.pos.config.config_color} !important
                }
                .ticket-screen .controls button, .ticket-screen button,#med_info .show-more, #med_info .show-less, .section-body .info-title,.pos .numpad button, .control-button, .pos .wk_popup .title,.pos .actionpad button,.show-pads, .product-info-url, .pharmacy-menu-bar .control-button, .pharma-order-options,.pos .order .summary{
                    background-color: white !important;
                    color: ${self.pos.config.config_color} !important;
                }
                .pos .orders .order-row:hover, .pos .orders .order-row.highlight, .ticket-screen .controls button.highlight, .search-box .wk-badge, .search-options li:hover, .pos .control-button.highlight, .pos .button.highlight, .pos .mode-button.selected-mode, #alternate_med_popup .product.selected, #alternate_med_popup .product.selected .price-tag{
                    background-color: ${self.pos.config.config_color} !important;
                    color: white !important;
                }
                #med_info .active{
                    border-bottom: ${self.pos.config.config_color} !important;
                    color: ${self.pos.config.config_color} !important;
                }
                .active, .wk_popup footer .button, .ticket-screen, .button, .pos .order .order-empty, .products-widget-control, .pos .breadcrumb-button{
                    color: ${self.pos.config.config_color} !important;
                }
                .search-section, .section-line{
                    border-color:${self.pos.config.config_color} !important;
                }
                .pos .numpad button:active{
                    background-color: Black !important;
                    color: white !important;
                }
                .pos .control-button.highlight, .pos .button.highlight, .ticket-screen .controls button.highlight{
                    background-color: ${self.pos.config.config_color} !important;
                    border-color: ${self.pos.config.config_color} !important;
                    color: white !important;
                }
                .fa-times-circle-o, .fa-medkit{
                    color: ${self.pos.config.config_color} !important;
                }
            `
            var styleSheet = document.createElement("style");
            styleSheet.innerText = styles;
            document.head.appendChild(styleSheet)
        }
        $('.pos .leftpane').on('dragover', function (e) {
            e.preventDefault();
            e.stopPropagation();
        })
        $('.pos .leftpane').on('drop', function (event) {
            var prod_id = event.originalEvent.dataTransfer.getData("text");
            var product = self.pos.db.get_product_by_id(prod_id);
            var order = self.pos.get_order();
            if (prod_id && product && order) {
                order.add_product(product,{});
            }
            event.originalEvent.dataTransfer.clearData();
            event.stopImmediatePropagation();
        });
        if(self.pos.config.product_display_type === 'list'){
            $('.product-list').removeClass('d-grid');
            $('.product-list').addClass('d-flex');
            $('.product-list').css('flex-direction', 'column');
        }
        this.pos.onClickHidePads();
    },
    async delete_current_order(){
        var order = this.currentOrder;
        if(order){
            const { confirmed } = await this.popup.add(ConfirmPopup, {
                title: 'Delete Order Confirmation',
                body: 'Do you want to Delete current Order?',
                confirmText: 'Yes',
                cancelText: 'No',
            });
            if (confirmed){
                var orders = this.pos.get_order_list();
                var index = orders.indexOf(order);
                this.pos.removeOrder(order);
                this.pos.set_order(orders[index+1] || orders[index-1] || orders[0]);
                if(this.pos.get_order_list().length === 0){
                    this.pos.add_new_order();
                }
            }
        }
    },
    async openCashTransferPopup() {
        const sessionId = this.pos.pos_session && this.pos.pos_session.id;
        if (!sessionId) {
            return this.popup.add(ErrorPopup, {
                title: "Sesión no encontrada",
                body: "Abrí una sesión POS antes de transferir.",
            });
        }
        try {
            const res = await this.env.services.orm.call("pos.session", "action_cash_transfer_from_config", [sessionId], {});

            await this.popup.add(ConfirmPopup, {
                title: "Transferencia realizada",
                body: `Se transfirieron ${res.amount}.\nAsiento: ${res.payment_name || "N/D"}`,
                confirmText: "OK",
            });
        } catch (err) {
            this.popup.add(ErrorPopup, {
                title: "No se pudo transferir",
                body: (err && err.message) || "Revisá configuración y permisos.",
            });
        }
    },

    async quick_pay(){
        var order = this.currentOrder;
        var quick_pay_method_id = this.pos.config.quick_pay_method[0];
        var payment_method = this.pos.payment_methods_by_id[quick_pay_method_id];

        if(order.orderlines.length === 0){
            this.popup.add(ErrorPopup, {
                title: 'No Orderlines',
                body: 'Please add some products first!!!',
            });
        }
        else if(!payment_method){
            this.popup.add(ErrorPopup, {
                title: 'Configure Quick Payment Method',
                body: 'Please add a Payment Method in Quick payment Configuration in Backend before using this Feature.',
            });
        }
        else{
            var res = await this.prescriptionproducts();
            if(res) this.done_payment(payment_method, order);
        }
    },
    async done_payment(payment_method, order){
        order.add_paymentline(payment_method);
        await this.pos.push_single_order(order);
        await this.pos.db.remove_unpaid_order(order);
        this.pos.showScreen('ReceiptScreen');
    },
    onClickEmptyOrder(){
        while(this.currentOrder && this.currentOrder.get_orderlines().length != 0){
            this.currentOrder.removeOrderline(this.currentOrder.get_orderlines()[0]);
        }
    },
    toggle_pharmacy_bar(){
        this.pos.show_bar === true ? this.pos.show_bar = false : this.pos.show_bar = true;
    },
    async prescriptionproducts(){
        var order = this.currentOrder;
        var prods = [];
        if (order) {
            order.get_orderlines().forEach(function (orderline) {
                if(orderline.product.is_prescription) prods.push(orderline.product.display_name);
            });
            if(prods.length){
                const { confirmed } = await this.popup.add(PrescriptionConfirmPopup, { prods });
                return confirmed;
            }return true;
        }
        return false;
    },
    async _onClickPay() {
        var res = await this.prescriptionproducts();
        if(res) super._onClickPay();
    },
    async _setValue(val) {
        var self = this;
        var line = self.pos.get_order().get_selected_orderline();
        if (line && line.refunded_orderline_id) {
            this.popup.add(ErrorPopup, {
                title: 'Quantity not changed',
                body: "You cannot make changes to the quantity of the orderline as it's and return order.",
            });
        }
        else {
            if (self.pos.numpadMode === 'quantity') {
                if (val == "") {
                    if (line) {
                        this.numberBuffer.reset();
                        self.pos.get_order().removeOrderline(line);
                        return 
                    }
                }
                else {
                    if (line !== undefined && line.product.product_price_by_uom.length && line.product.manage_multi_uom_via_price) {
                        var selected_orderline = line
                        this.popup.add(ShowUomOptionsPopup, {
                            title: 'Medicine Units',
                            line: line,
                            selected_uom_id: selected_orderline.uom_id,
                            previous_unit: line.product.uom_po_id
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

patch(CategorySelector.prototype, {
    setup(){
        this.pos = usePos();
        this.popup = useService("popup");
    },
    async onClickAdvanceSearch() {
        this.popup.add(AdvanceMedicineSearchPopup, {
            title: "Advance Search(Medicine)",
            cancelText: "Cancel",
        });
    }
});

patch(ProductsWidget, {
    components: { ...ProductsWidget.components, WkProductCard },
});

patch(ProductsWidget.prototype, {
    get productsToDisplay() {
        var self = this;
        var products = [];
        var result = super.productsToDisplay;
        var search_salt = self.state.search_salt;
        var advance_search = this.pos.data_to_display;
        var list = this.pos.db.get_product_by_category(this.selectedCategoryId);

        if(advance_search){
            var advance_search_products = [];
            list.forEach(product => {
                if(product.manufacturer_id){
                    if(advance_search.manufacturer.includes(product.manufacturer_id[0])){
                        advance_search_products.push(product)
                    }
                }
                if(product.salt_composition_ids.length){
                    product.salt_composition_ids.forEach(salt_id => {
                        if(advance_search.salt_composition.includes(salt_id)){
                            advance_search_products.push(product)
                        }
                    });
                }
                if(product.salt_ids.length){
                    product.salt_ids.forEach(salt_id => {
                        if(advance_search.basic_salt.includes(salt_id)){
                            advance_search_products.push(product)
                        }
                    });
                }
                if(product.medicine_salt_ids.length){
                    product.medicine_salt_ids.forEach(salt_id => {
                        if(advance_search.medicine_salt.includes(salt_id)){
                            advance_search_products.push(product)
                        }
                    });
                }
                if(product.medicine_usage_ids.length){
                    product.medicine_usage_ids.forEach(usage_id => {
                        if(advance_search.medicine_usage.includes(usage_id)){
                            advance_search_products.push(product)
                        }
                    });
                }
                if(product.side_effects_ids.length){
                    product.side_effects_ids.forEach(side_effect_id => {
                        if(advance_search.side_effects.includes(side_effect_id)){
                            advance_search_products.push(product)
                        }
                    });
                }
                if(product.safety_advice_ids.length){
                    product.safety_advice_ids.forEach(advice_id => {
                        if(advance_search.safety_advices.includes(advice_id)){
                            advance_search_products.push(product)
                        }
                    });
                } 
            });
            advance_search_products = [...new Set(advance_search_products)];
            return advance_search_products
        }else{
            if(search_salt){
                list.forEach(product => {
                    search_salt = self.state.search_salt.toLowerCase().trim();
                    var search_terms = product.medicine_search_term;

                    if(search_terms && search_terms.search(search_salt) !== -1){
                        products.push(product);
                    }
                });
            }
            result = [...new Set([...result, ...products])]
            return result;
        }
    },
    _updateSearch(event) {
        this.state.search_salt = event.detail;
        this.state.searchWord = event.detail;
    },
});

patch(ProductCard.prototype, {
    setup(){
        super.setup(...arguments);
        this.pos = usePos();
        this.popup = useService("popup");
        onMounted(this.onMounted);
    },
    onMounted() {
        var self = this;
        $('.pos .product').attr('draggable', 'True');
        $('.pos .product img').attr('draggable', 'False');

        $('.pos .product').on('dragstart', function (event) {
            event.originalEvent.dataTransfer.clearData();
            event.originalEvent.dataTransfer.setData("text", event.currentTarget.dataset.productId);
        });
    },
    async onMedProductInfoClick(product) {
        const info = await this.pos.getProductInfo(product, 1);
        var stocks = await this.pos.getProductStocks(product.id);
        if(stocks) product.stocks = stocks;
        this.popup.add(MedicineProductInfoPopup, { info: info , product: product });
    }
});

patch(PartnerListScreen.prototype, {
    get partners() {
        var res = super.partners;
        const filteredArray = res.filter(customer => {
            if (this.props.doctor) {
                return customer.is_a_doctor;
            } else {
                return !customer.is_a_doctor;
            }
        });
        return filteredArray
    },

    async getNewPartners() {
        let domain = [];
        const limit = 30;
        if (this.state.query) {
            const search_fields = ["name", "parent_name", "phone_mobile_search", "email", "numero_matricula"];
            domain = [
                ...Array(search_fields.length - 1).fill('|'),
                ...search_fields.map(field => [field, "ilike", this.state.query + "%"])
            ];
        }
        const result = await this.orm.silent.call(
            "pos.session",
            "get_pos_ui_res_partner_by_params",
            [[odoo.pos_session_id], { domain, limit: limit, offset: this.state.currentOffset }]
        );
        return result;
    },

    async saveChanges(processedChanges) {
        if (this.props.doctor) {
            processedChanges['is_a_doctor'] = true;
        }
        return super.saveChanges(...arguments);
    }
});

patch(TicketScreen.prototype, {
    getSelectedDoctor() {
        const order = this.getSelectedOrder();
        return order ? order.get_doctor() : null;
    },
    async onDoRefund() {
        const order = this.getSelectedOrder();
        if (order && this._doesOrderHaveSoleItem(order)) {
            if (!this._prepareAutoRefundOnOrder(order)) return;
        }
        if (!order) {
            this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
            return;
        }
        const partner = order.get_partner();
        const doctor = order.get_doctor();

        const allToRefundDetails = this._getRefundableDetails(partner);
        if (allToRefundDetails.length == 0) {
            this._state.ui.highlightHeaderNote = !this._state.ui.highlightHeaderNote;
            return;
        }
        const destinationOrder = this.props.destinationOrder && partner === this.props.destinationOrder.get_partner() &&
            !this.pos.doNotAllowRefundAndSales() ? this.props.destinationOrder : this._getEmptyOrder(partner);

        for (const refundDetail of allToRefundDetails) {
            const product = this.pos.db.get_product_by_id(refundDetail.orderline.productId);
            const options = this._prepareRefundOrderlineOptions(refundDetail);
            await destinationOrder.add_product(product, options);
            refundDetail.destinationOrderUid = destinationOrder.uid;
        }

        if (order.fiscal_position_not_found) {
            this.showPopup("ErrorPopup", {
                title: _t("Fiscal Position not found"),
                body: _t("The fiscal position used in the original order is not loaded. Make sure it is loaded by adding it in the pos configuration."),
            });
            return;
        }
        destinationOrder.fiscal_position = order.fiscal_position;
        this.setPartnerToRefundOrder(partner, destinationOrder);
        if (doctor && !destinationOrder.get_doctor()) {
            destinationOrder.set_doctor(doctor);
        }

        if (this.pos.get_order().cid !== destinationOrder.cid) {
            this.pos.set_order(destinationOrder);
        }
        this.closeTicketScreen();
    },
});