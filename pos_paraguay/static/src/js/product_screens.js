/** @odoo-module **/

import { registry } from "@web/core/registry";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";

patch(ProductScreen.prototype, {
    async _getProductByBarcode(code) {
        console.log("Codigo de barras a buscar:", code);

        let codigo_antes = code.code;
        let codigo_modificado = codigo_antes.replace(/%/g, ""); // Remueve los '% en teoria'
        console.log("Codigo Modificado:", codigo_modificado);

        code.code = codigo_modificado;
        code.base_code = codigo_modificado;

        console.log("Code despues de modificacion:", code);

        return super._getProductByBarcode(...arguments);
    }
});

