/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { Order, Orderline } from "@point_of_sale/app/store/models";

patch(Order.prototype, {
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        var doctor;
        if (json.doctor) {
            doctor = this.pos.db.get_partner_by_id(json.doctor);
            if (!doctor) console.error("ERROR: trying to load a doctor not available in the pos");
        } else doctor = null;
        this.set_doctor(doctor);
    },
    export_as_JSON (){
        var json = super.export_as_JSON(...arguments);
        json.doctor = this.get_doctor() ? this.get_doctor().id : false;
        return json;
    },
    get_doctor(){
        return this.doctor;
    },
    set_doctor(doctor){
        this.doctor = doctor;
    },
    
    // Método mejorado para agregar productos con UoM
    async add_product(product, options) {
        if (options && options.selectedUomLine) {
            // Configurar el producto temporalmente con la UoM seleccionada
            product._selectedUomLine = options.selectedUomLine;
        }
        
        const orderline = await super.add_product(product, options);
        
        // Aplicar configuración de UoM a la línea creada
        if (orderline && product._selectedUomLine) {
            const uomLine = product._selectedUomLine;
            orderline.uom_line = uomLine;
            orderline.uom_id = uomLine.uom_id[0];
            orderline.secondary_uom_id = uomLine.uom_id[0];
            orderline.set_unit_price(uomLine.unit_price);
            orderline.price_type = "manual";
            
            // Limpiar la configuración temporal
            delete product._selectedUomLine;
        }
        
        return orderline;
    }
});

// patch(Orderline.prototype, {
//     init_from_JSON(json) {
//         super.init_from_JSON(...arguments);
//         this.uom_id = json.uom_id;
//         this.secondary_uom_id = json.secondary_uom_id;
//         this.product_uom_id = json.product_uom_id;
//         this.previous_uom_id = json.previous_uom_id;
//         this.uom_line = json.uom_line;
//     },
    
//     export_as_JSON (){
//         var json = super.export_as_JSON(...arguments);
        
//         // Información básica de UOM
//         if (this.uom_id) json.uom_id = this.uom_id;
//         if (this.secondary_uom_id) json.secondary_uom_id = this.secondary_uom_id;
//         if (this.product_uom_id) json.product_uom_id = this.product_uom_id;
//         if (this.previous_uom_id) json.previous_uom_id = this.previous_uom_id;
        
//         // Información específica de farmacia
//         if (this.uom_line) {
//             json.uom_line = this.uom_line;
//             // La cantidad que se envía es la cantidad de "paquetes" que ingresó el usuario
//             // El backend calcula la cantidad real multiplicando por uom_line.qty
//         }
        
//         return json;
//     },
    
//     set_unit(uom_id) {
//         this.uom_id = uom_id;
//     },
    
//     getDisplayData() {
//         return {
//             id: this.id,
//             productName: this.get_full_product_name(),
//             price: this.env.utils.formatCurrency(this.get_display_price()),
//             qty: this.get_quantity_str(),
//             unit: this.get_unit().name,
//             previous_uom_id: this.product_uom_id,
//             unitPrice: this.env.utils.formatCurrency(this.get_unit_display_price()),
//             oldUnitPrice: this.env.utils.formatCurrency(this.get_old_unit_display_price()),
//             discount: this.get_discount_str(),
//             customerNote: this.get_customer_note(),
//             internalNote: this.getNote(),
//             comboParent: this.comboParent?.get_full_product_name(),
//             imageUrl: this.get_product().getImageUrl(),
//             is_medicine: this.get_product().is_medicine,
//             product: this.get_product(),
//             is_refund: this.hasOwnProperty('refunded_qty'),
//         };
//     }
// });