/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { onMounted, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class AdvanceMedicineSearchPopup extends AbstractAwaitablePopup {
    static template = "pos_pharmacy_management.AdvanceMedicineSearchPopup";

    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(this.onMounted);
        Object.assign(this, this.props.info);

        this.state = useState({
            manufacturerSearchInput: '',
            saltCompSearchInput: '',
            basicSaltSearchInput: '',
            medSaltSearchInput: '',
            medUsageSearchInput: '',
            sideEffectsSearchInput: '',
            safetyAdvicesSearchInput: '',
        });
        this.pos.data_to_search = {
            'manufacturer' : [],
            'medicine_salt' : [],
            'salt_composition': [],
            'basic_salt': [],
            'medicine_usage': [],
            'safety_advices': [],
            'side_effects': [],
        }
        if(this.pos.data_to_display){
            this.pos.data_to_search = this.pos.data_to_display;
        }
    }
    onMounted(){
        var self = this;
        $('.search-box input').on('keyup', function(ev) {
            var data = self.pos.data_to_search[ev.currentTarget.name];
            var count = data.length;
            var val = $(ev.currentTarget).val();
            var search_section = $(ev.currentTarget).parents('.search-section').children('.search-options');
            if(ev.key === 'Backspace' && count && !val){
                data.pop();
                search_section.css({'display' : 'none'});
            }
            search_section.css({'display' : 'block'});
        });
        $('.advance_med_body').on('click', function(ev) {
            $('.search-options').css({'display' : 'none'});
        });
        $('.search-section').on('click', function(ev) {
            ev.stopPropagation();
            ev.preventDefault();
        });
    }
    async confirm(event) {
        if (this.pos.data_to_search.basic_salt.length !== 0 || this.pos.data_to_search.manufacturer.length || this.pos.data_to_search.medicine_salt.length || this.pos.data_to_search.salt_composition.length || this.pos.data_to_search.medicine_usage.length || this.pos.data_to_search.safety_advices.length || this.pos.data_to_search.side_effects.length) {
            this.pos.data_to_display = this.pos.data_to_search;
            this.pos.advanced_search_active = true;
            this.cancel();
        }
        else {
            this.cancel();
        }
    }
    async clear_advance_search(){
        this.pos.data_to_display = "";
        this.pos.advanced_search_active = false;
        this.cancel();
    }
    show(input, value){
        var str = String(value.name).toLowerCase();      
        var res = str.includes(input.toLowerCase()) ? true : false;
        return res;
    }
    add_to_search(ev, search, key, value){
        this.state[search] = '';            
        if(!this.pos.data_to_search[key].includes(value)){
            this.pos.data_to_search[key].push(value);
        }
        $(ev.currentTarget).parents('.search-section').children('.search-options').css({'display' : 'none'});
    }
    remove_from_search(key, value){
        if (this.pos.data_to_search[key].includes(value)) {
            this.pos.data_to_display = '';
            var index = this.pos.data_to_search[key].indexOf(value);
            this.pos.data_to_search[key].splice(index, 1);
        }
    }
    onfocus(ev){
        $('.search-options').css({'display' : 'none'});
        $(ev.currentTarget).parents('.search-section').children('.search-options').css({'display' : 'block'});
    }
    onfocusout(ev, key){
        this.state[key] = '';
        $(ev.currentTarget).parents('.search-section').children('.search-options').css({'display' : 'none'});
    }
    get_placeholder(key, count){
        var res = count > 0 ? '' : `Search for ${key}`;
        return res;
    }
    clear_search(ev, key){
        this.state[key] = '';
        $(ev.currentTarget).parents('.search-section').children('.search-options').css({'display' : 'none'});
    }
}
