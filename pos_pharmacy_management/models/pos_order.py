# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import fields, models, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    doctor = fields.Many2one('res.partner', 'Doctor')

    @api.model
    def _order_fields(self, ui_order):
        data = super(PosOrder, self)._order_fields(ui_order)
        data.update({ 'doctor': ui_order.get('doctor', False) })
        return data

    def _export_for_ui(self, order):
        result = super(PosOrder, self)._export_for_ui(order)
        result['doctor'] = order.doctor.id
        return result

    @api.model
    def _get_invoice_lines_values(self, line_values, pos_order_line):
        if(pos_order_line.secondary_qty):
            return {
                "product_id": line_values["product"].id,
                "quantity": line_values["quantity"],
                "discount": line_values["discount"],
                "secondary_qty": pos_order_line.secondary_qty,
                "price_unit": line_values["price_unit"],
                "name": line_values["name"],
                "tax_ids": [(6, 0, line_values["taxes"].ids)],
                "product_uom_id": line_values["uom"].id,
            }
        else:
            return super(PosOrder, self)._get_invoice_lines_values(line_values,pos_order_line)


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    secondary_qty = fields.Float('Quantity', digits='Product Unit of Measure', default=1)
    secondary_uom_id = fields.Many2one("uom.uom", string="Secondary UOM Quantity")

    @api.model
    def _order_line_fields(self, line, session_id=None):
        fields_return = super(PosOrderLine, self)._order_line_fields(line, session_id=None)
        
        if line and line[2] and line[2].get('uom_id'):
            uom_id = line[2].get('uom_id')
            uom = self.env['uom.uom'].browse(uom_id)
            product_id = line[2].get('product_id')
            product = self.env['product.product'].browse(product_id)
            qty_entered = line[2].get('qty', 1)
            
            if uom and product:
                # Verificar si es una UOM personalizada de farmacia
                if product.manage_multi_uom_via_price and product.product_price_by_uom:
                    # Buscar la configuaracion de precio por UOM
                    uom_price_line = self.env['product.uom.price'].search([
                        ('variant', '=', product.product_tmpl_id.id),
                        ('uom_id', '=', uom_id)
                    ], limit=1)
                    
                    if uom_price_line:
                        # Calcular la cantidad real basada en la configuracion de farmacia
                        # qty_entered es la cantidad de "paquetes" ej: 1 paquete de 50 tabletas
                        # uom_price_line.qty es cuantas unidades base hay en cada paquete
                        real_qty = qty_entered * uom_price_line.qty
                        
                        fields_return[2].update({
                            'secondary_qty': real_qty,  # Cantidad real en unidades base
                            'secondary_uom_id': uom_id,
                            'uom_id': uom_id,
                            'qty': qty_entered  # Cantidad de paquetes ingresada
                        })
                    else:
                        # Fallback
                        try:
                            converted_qty = uom._compute_quantity(qty_entered, product.uom_id)
                        except:
                            converted_qty = qty_entered
                        fields_return[2].update({
                            'secondary_qty': converted_qty,
                            'secondary_uom_id': uom_id,
                            'uom_id': uom_id
                        })
                else:
                    # converison de UOM
                    try:
                        converted_qty = uom._compute_quantity(qty_entered, product.uom_id)
                    except:
                        converted_qty = qty_entered
                    fields_return[2].update({
                        'secondary_qty': converted_qty,
                        'secondary_uom_id': uom_id,
                        'uom_id': uom_id
                    })
        else:
            # No hay UOM personalizada, usar la UOM base del producto
            product_id = line[2].get('product_id')
            if product_id:
                product = self.env['product.product'].browse(product_id)
                fields_return[2].update({
                    'uom_id': product.uom_id.id,
                    'secondary_qty': line[2].get('qty', 1)
                })
                
        return fields_return

    def get_product_uom(self, product_id):
        product = self.env['product.product'].browse(product_id)
        return product.uom_id

    def _export_for_ui(self, orderline):
        result = super(PosOrderLine, self)._export_for_ui(orderline)
        result["secondary_uom_id"] = orderline.secondary_uom_id
        result["secondary_qty"] = orderline.secondary_qty
        return result


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    secondary_qty = fields.Float(
        string="Quantity",
        compute="_compute_quantity",
        store=True,
        readonly=False,
        precompute=True,
        digits="Product Unit of Measure",
        help="The optional quantity expressed by this line, eg: number of product sold. "
        "The quantity is not a legal requirement but is very useful for some reports.",
    )
    
    @api.onchange("secondary_qty")
    def _onchage_qty_pharmacy(self):
        self.quantity = self.secondary_qty

    @api.depends("display_type")
    def _compute_quantity(self):
        for line in self:
            if line.display_type == "product":
                line.secondary_qty = line.secondary_qty if line.secondary_qty else 1
            else:
                line.secondary_qty = False


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_stock_move_vals(self, first_line, order_lines):
        res = super(StockPicking, self)._prepare_stock_move_vals(first_line, order_lines)
        
        # Calcular la cantidad total correctamente
        total_qty = 0
        for line in order_lines:
            if hasattr(line, 'secondary_qty') and line.secondary_qty:
                # Usar secondary_qty que ya tiene la conversion correcta
                total_qty += abs(line.secondary_qty)
            else:
                # Fallback a quantity normal
                total_qty += abs(line.qty)
        
        if total_qty > 0:
            res.update({"product_uom_qty": total_qty})
            
        return res