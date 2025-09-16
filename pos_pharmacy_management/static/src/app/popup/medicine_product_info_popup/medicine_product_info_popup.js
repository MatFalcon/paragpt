/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { AlternateMedicinePopup } from "@pos_pharmacy_management/app/popup/alternate_medicine_popup/alternate_medicine_popup";

export class MedicineProductInfoPopup extends AbstractAwaitablePopup {
    static template = "pos_pharmacy_management.MedicineProductInfoPopup";

    setup() {
        super.setup();
        this.pos = usePos();
        this.popup = useService("popup");
        onMounted(this.onMounted);
        Object.assign(this, this.props.info);
    }
    onMounted(){
        $($('.heading')[0]).addClass('active');

        var head_bar = document.getElementById('head_bar');
        var content = document.getElementById('content');
        var head_width = head_bar.scrollWidth;
        var lastScrollTop = 0;

        $('.fa-angle-left').on('click', function(ev) {
            head_bar.scrollBy(-head_width, 0);
            content.scrollTop = -content.scrollHeight;
        });
        $('.fa-angle-right').on('click', function(ev) {
            head_bar.scrollBy(head_width, 0);
            content.scrollTop = content.scrollHeight;
        });
        $('.heading').on('click', function(ev) {
            $('.heading.active').removeClass('active');
            $(ev.currentTarget).addClass('active');

            var id = $(this).attr('href');
            var diff = $($('.section')[0]).offset().top;
            var move = $(`${id}`).offset().top;

            $('#content').animate({
                scrollTop: move - diff
            }, 100);
        });
        $('#content').on('scroll', function(ev){
            var scrollPos = $('#content').scrollTop();
            var diff = $($('.section')[0]).offset().top;
            $('.heading').each(function () {
                var currLink = $(this);
                var refElement = $(currLink.attr("href"));
                if(refElement.position()){
                    var ref = refElement.position().top - diff;
                    if (ref <= scrollPos && ref + refElement.height() > scrollPos) {
                        $('.heading').removeClass('active');
                        currLink.addClass("active");
                        
                        if(scrollPos > lastScrollTop) head_bar.scrollBy(100, 0);
                        else head_bar.scrollBy(-100, 0);
                    }
                    else{
                        currLink.removeClass("active");
                    }
                }
            });
            lastScrollTop = scrollPos;
        })
    }
    show_more(ev){
        var info_card = $(ev.currentTarget).parent()
        var info_block = info_card.children('.info-block');
        var show_less = info_card.children('.show-less');
        $(info_block).css({ 'max-height' : 'fit-content', 'line-height' : '2rem'});
        $(show_less).css({ 'display' : 'block' });
        $(ev.currentTarget).css({'display' : 'none'})
    }
    show_less(ev){
        var info_card = $(ev.currentTarget).parent();
        var info_block = info_card.children('.info-block');
        var show_more = info_card.children('.show-more');
        $(info_block).css({ 'max-height' : '60px'});
        $(show_more).css({'display' : 'block'});
        $(ev.currentTarget).css({'display' : 'none'});
    }
    async onAlternateMedicineClick(product) {
        this.cancel();
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
        this.cancel();
        this.popup.add(AlternateMedicinePopup, {product : product, med_ids : med_ids});
    }
    get expirationDate(){
        var date = new Date(this.stock.expiration_date);
        return date.toLocaleDateString();
    }
}
