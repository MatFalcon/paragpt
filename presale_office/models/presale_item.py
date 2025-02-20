# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api , _
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)
# _logger.info('Computing net amount for vouchers %s' % voucher_ids)
class PresaleOrderHeadling(models.Model):
    _name = "presale.order.heading"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", tracking=True, copy=True)
    order_id = fields.Many2one('presale.order', string="Order Id", store=True, tracking=True, copy=True)
    item_id = fields.One2many('presale.order.item', 'heading_id', string="Items", tracking=True, copy=True)


    assign_minor_materials = fields.Boolean(string="Assign (No/Yes)?", default=False, tracking=True, copy=True)
    template_minor_perc = fields.Float(string="Percent %", tracking=True, copy=True)

    presale_item_template = fields.Boolean(string="Assign Template?", tracking=True, copy=True)

    item_template_ids = fields.Many2one('presale.order.heading', string="Template Associated", tracking=True, copy=True)
    create_item_template = fields.Boolean(string="Create Template?", tracking=True, copy=True)


    def set_minor_material(self):
        for rec in self:
            get_materials = rec.item_id.filtered(lambda x: x.creado_por_boton is False and x.create_labor is False and x.is_minor_materials is False and x.create_labor is False)
            if not get_materials:
                raise ValidationError("No se puede agregar una línea de Materiales Menores sin haber creado un Item (No M.O como producto)!")
            else:
                print("HAY MATERIALES")
                get_fixed_minor_material = rec.item_id.filtered(lambda x: x.creado_por_boton is False and x.create_labor is False and x.is_minor_materials is True and x.create_labor is False)
                if get_fixed_minor_material:
                    raise ValidationError("Ya se encuentra registrado un Item de Materiales Menores de manera fija para este Rubro!")
                else:
                    get_material = sum(get_materials.mapped('price_subtotal'))
                    presale_minor_material = self.env['product.template'].search([('is_minor_material', '=', True)])
                    if presale_minor_material:
                        minor_mat_tag = self.env['account.account.tag'].search([('is_minor_material_tag','=', True)])
                        existing_line = rec.item_id.filtered(lambda x: x.creado_por_boton is True and x.create_labor is False and x.is_minor_materials is False and x.create_labor is False)
                        if not existing_line:
                            print("CREA LINEA DE MATERIAL MENOR")
                            new_item = self.env['presale.order.item'].create({
                                'heading_id': rec.id,
                                'name': 'MATERIALES MENORES',
                                'total_item_qty': 1,
                                'creado_por_boton': True,
                            })

                            values = {
                                'item_id': new_item.id,
                                'product_id': presale_minor_material.id,
                                'unit_price': get_material * (rec.template_minor_perc / 100),
                                'qty': 1,
                                'account_analytic_id': [((6, 0, [minor_mat_tag.id]))] if minor_mat_tag else False
                            }
                            new_item.detail_ids.create(values)
                            print("CREADO")
                        else:
                            print("ACTUALIZA LINEA DE MATERIAL MENOR")
                            existing_line.write({
                                'unit_price':  get_material * (rec.template_minor_perc / 100),
                                'qty':1,
                                'account_analytic_id': [((6, 0, [minor_mat_tag.id]))] if minor_mat_tag else False
                            })


    def select_item_template(self):
        for rec in self:
            if not rec.item_template_ids:
                raise ValidationError( "No se puede estirar una plantilla sin antes haber seleccionado o generado uno valido!")
            else:
                selected_template = rec.item_template_ids
                for existing_item in rec.item_id:
                    existing_item.detail_ids.unlink()
                    existing_item.unlink()

                print("CREACION")
                for st in selected_template:
                    head_template_val = {
                        'name': st.name
                    }
                    print(f"[HEADING_GEN:] {head_template_val}")
                    for item in st.item_id:
                        item_value = self.env['presale.order.item'].create({
                            'heading_id': rec.id,
                            'name': item.name,
                            'code': item.code,
                            'total_item_qty': item.total_item_qty,
                            'creado_por_boton': item.creado_por_boton,
                            'create_labor': item.create_labor,
                            'is_minor_materials': item.is_minor_materials,
                            'has_labour': item.has_labour,
                            'is_fixed_labor': item.is_fixed_labor,
                            'material_additionals_id': item.material_additionals_id.id,
                            'labour_additionals_id': item.labour_additionals_id.id
                        })
                        for dt in item.detail_ids:
                            account_analytic_ids = [((6, 0, dt.account_analytic_id.ids))]
                            detail_values = {
                                'item_id': item_value.id,
                                'headling_id': item_value.heading_id.id,
                                'order_id': item_value.order_id.id,
                                'product_id': dt.product_id.id,
                                'unit_price': dt.unit_price,
                                'qty': dt.qty,
                                'account_analytic_id': account_analytic_ids
                            }
                            item_value.detail_ids.create(detail_values)
    

class CategoriaProducto(models.Model):
    _inherit = "product.category"

    preventa_item_id = fields.One2many("presale.order.item", "categ_id")

class PreSaleOrderItem(models.Model):
    _name = 'presale.order.item'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Name", copy=True)
    product_name = fields.Char("Nombre Producto")
    product_id = fields.Many2one('product.product',string="Product", tracking=True, copy=True, context={'create': False})
    heading_id = fields.Many2one('presale.order.heading','Presale Headling', store=True, copy=True)
    order_id = fields.Many2one(related='heading_id.order_id', string='Presale Order', store=True, copy=True)

    code = fields.Char(string="Code", copy=True)

    assign_minor_materials = fields.Boolean(string="Assign (No/Yes)?", default=False, tracking=True, copy=True)
    template_minor_perc = fields.Float(string="Percent %", tracking=True, copy=True)

    presale_item_template = fields.Boolean(string="Assign Template?", tracking=True, copy=True)
    create_item_template = fields.Boolean(string="Create Template?", tracking=True, copy=True)
    item_template_ids = fields.Many2one('presale.order.item', string="Template Associated", tracking=True, copy=True)
    total_item_qty = fields.Float(string="Qty.")

    es_producto_temporal = fields.Boolean()
    # para ficha de producto
    detailed_type = fields.Selection(
        [('consu', 'Consumible'),
         ('servicio', 'Servicio'),
         ('product', 'Producto Almacenable')]
    )
    categ_id = fields.Many2one("product.category")
    ####### CALCULOS PREVENTAS ########
    imprevisto_valores = {
        'importados':0.03,
        'fabricacion':0.05,
        'tercerizados':0.02,
    }
    imprevisto_valor = fields.Float(string="% de imprevisto")
    imprevisto = fields.Selection([('importados', 'Importados'), ('fabricacion', 'Fabricacion'), ('tercerizados', 'Tercerizados')], string='Imprevistos', required=True)
    uom_id = fields.Many2one('uom.uom',string="Uom", tracking=True, copy=True)
    qty = fields.Float(string="Quantity", tracking=True, copy=True, default=1)

    # COSTOS UNITARIOS PREVENTA
    standard_price = fields.Float(string="Costo unit", compute="_compute_costos_unitarios")
    imprevisto_calculo = fields.Float(string="Valor", compute="_compute_costos_unitarios")
    total_cost_item = fields.Float(string="Sub total Unit", compute="_compute_costos_unitarios")#, compute="_compute_subtotal_items"
    precio_venta_margen_unit = fields.Float(string="Total Unit Venta", compute="_compute_costos_unitarios")


    margen_venta = fields.Float(string="Margen", default=2.42, readonly=True)
    # PRECIOS VENTA
    total_sin_descuento = fields.Float(string="Total Sin Descuento", compute="_compute_precios_venta")
    margen_sin_descuento = fields.Float(string="Margen Sin descuento", compute="_compute_precios_venta")
    margen_porcentaje_sin_descuento = fields.Float(compute="_compute_precios_venta")

    # CON DESCUENTO
    precio_unit_dcto = fields.Float(string="Precio Unit Con Dcto", compute="_compute_precios_venta")
    total_con_descuento = fields.Float(string="Total con Descuento", compute="_compute_precios_venta")
    margen_con_descuento = fields.Float(string="Margen con Descuento", compute="_compute_precios_venta")
    margen_porcentaje_con_descuento = fields.Float(compute="_compute_precios_venta")


    unit_price = fields.Float(string="Unit Mat.", compute="calculate_presale_factors", store=True, tracking=True, copy=True)
    price_subtotal = fields.Float(string="Subtotal Mat.", compute="calculate_presale_factors", store=True, copy=True)

    porcentaje_descuento = fields.Float(string="Descuento", default=10)  # 10%

    labor_unit_price = fields.Float(string="Unit Lab.", compute="calculate_presale_factors", store=True, tracking=True, copy=True)
    labor_unit_price_edit = fields.Float(string="Unit Lab.", tracking=True, copy=True)
    labor_percent = fields.Float(string="% Labour", tracking=True,  copy=True)
    labor_subtotal_price = fields.Float(string="Subtotal Lab.", compute="calculate_presale_factors", store=True, copy=True)

    unforseen_unit_material = fields.Float(string="Unit", compute="calculate_presale_factors", store=True, copy=True)
    unforseen_subtotal_material = fields.Float(string="Subtotal", compute="calculate_presale_factors", store=True, copy=True)
    unforseen_unit_labor = fields.Float(string="Unit",  compute="calculate_presale_factors", store=True, copy=True)
    unforseen_subtotal_labor = fields.Float(string="Subtotal", compute="calculate_presale_factors", store=True, copy=True)

    mat_unit_price_final = fields.Float(string="Materiales", compute="calculate_presale_factors",  copy=True)
    mat_subtotal_price_final = fields.Float(string="Precio Unitario",  compute="calculate_presale_factors", copy=True)
    lab_unit_price_final = fields.Float(string="Mano de Obra", compute="calculate_presale_factors", copy=True)
    lab_subtotal_price_final = fields.Float(string="Subtotal", compute="calculate_presale_factors", copy=True)
    creado_por_boton = fields.Boolean(string="Creado por Boton", default=False, copy=True)

    account_analytic_id = fields.Many2many('account.account.tag', string="Etiquetas Analíticas", required=True, tracking=True, copy=True)
    minor_materials_percent = fields.Float(string="Minor Materials %", tracking=True, copy=True)

    material_additionals_id = fields.Many2one('presale.types_additionals', string="Factor - Precio de Venta - Mat.", tracking=True, copy=True)
    labour_additionals_id = fields.Many2one('presale.types_additionals', string="Factor - Precio de Venta - M.O", tracking=True, copy=True)

    total_material_and_labour = fields.Float(string='Total Mat. and Lab.', compute="calculate_presale_factors", store=True, tracking=True, copy=True)
    total_mat_lab_unforseen = fields.Float(string="Total Unforseen Mat. and Unforseen Lab.", compute="calculate_presale_factors", store=True, copy=True)
    create_labor = fields.Boolean(string="Create Labour", default=False, copy=True)

    is_fixed_labor = fields.Boolean(string="Is fixed labour?", copy=True)
    is_fixed_labor_unit = fields.Boolean(string="Editar M.O", default=False, copy=True)
    is_minor_materials = fields.Boolean(string="Is Minor Materials?", default=False, copy=True)
    has_labour = fields.Boolean(string="Has Labour?", default=False, copy=True)

    items_type_action = fields.Selection([('mop', 'Mano de Obra como Producto'), ('mm', 'Materiales Menores'),('mco', 'Materiales (Con M.O)'), ('mso', 'Materiales (Sin M.O)')], default="mco", string="Tipo de Producto", tracking=True, copy=True)
    id_distribuited_lines = fields.Boolean(string="Is Distribuited lines", default=False)
    image_128 = fields.Image(string="Image")
    rounding_factor = fields.Integer("Múltiplo de Redondeo", default=2)



    """
        Don't fucking care about your situation... I'm not here anymore
    """

    # ----- Orden Preventa -----
    presale_order_id = fields.Many2one("presale.order", string="Orden Preventa")
    # -----  Detalle Item  -----
    detail_ids = fields.One2many('presale.order.item.detail', 'item_id', copy=True)

    # -----  Sub Totales  -----
    total_venta_margen_item = fields.Float(string="Total Venta Margen") #, compute="_compute_subtotal_items"
    
    @api.onchange("name", "product_id")
    def _onchange_nombre(self):
        for rec in self:
            if rec.name:
                rec.es_producto_temporal = True
            else:
                rec.es_producto_temporal = False

    @api.onchange('imprevisto')
    def onchange_imprevistos(self):
        for record in self:
            if record.imprevisto == 'importados':
                record.imprevisto_valor = 3
            elif record.imprevisto == 'fabricacion':
                record.imprevisto_valor = 5
            elif record.imprevisto == 'tercerizados':
                record.imprevisto_valor = 2

    @api.depends("imprevisto", "imprevisto_valor", "total_cost_item", "precio_venta_margen_unit", "standard_price",
                 "margen_venta", "rounding_factor")
    def _compute_costos_unitarios(self):
        for record in self:
            record.standard_price = sum(linea.total_cost or 0 for linea in record.detail_ids)
            record.imprevisto_calculo = 0
            record.total_cost_item = 0
            record.precio_venta_margen_unit = 0

            _logger.info("Entra en _compute_costos_unitarios")

            if record.imprevisto and record.standard_price > 0:
                _logger.info("Se calculan los costos y precios unitarios")
                imprevisto_valor = record.imprevisto_valor / 100

                record.imprevisto_calculo = record.standard_price * imprevisto_valor
                record.total_cost_item = record.imprevisto_calculo + record.standard_price

                record.precio_venta_margen_unit = round(
                    record.total_cost_item * record.margen_venta / record.rounding_factor
                ) * record.rounding_factor

                _logger.info(f"precio_venta_margen_unit: {record.precio_venta_margen_unit}")

    @api.depends("total_sin_descuento", "margen_sin_descuento", "margen_porcentaje_sin_descuento",
                 "precio_unit_dcto", "total_con_descuento", "margen_con_descuento", "margen_porcentaje_con_descuento",
                 "porcentaje_descuento", "rounding_factor")
    def _compute_precios_venta(self):
        for record in self:
            if record.imprevisto and record.standard_price > 0:
                record.total_sin_descuento = record.precio_venta_margen_unit
                record.margen_sin_descuento = record.total_sin_descuento - record.total_cost_item
                record.margen_porcentaje_sin_descuento = (
                            record.margen_sin_descuento / record.total_sin_descuento) if record.total_sin_descuento else 0

                precio_unit_dcto = record.precio_venta_margen_unit * (1 - (record.porcentaje_descuento / 100))
                _logger.info(f"precio_unit_dcto antes de redondeo: {precio_unit_dcto}")

                rounding_factor = record.rounding_factor if record.rounding_factor > 0 else 1
                record.precio_unit_dcto = round(precio_unit_dcto / rounding_factor) * rounding_factor
                _logger.info(f"precio_unit_dcto después de redondeo ({rounding_factor}): {record.precio_unit_dcto}")

                record.total_con_descuento = record.precio_unit_dcto
                record.margen_con_descuento = record.total_con_descuento - record.total_cost_item

                _logger.info(f"qty: {record.qty} - precio_unit_dcto: {record.precio_unit_dcto}")
                _logger.info(
                    f"margen_con_descuento: {record.margen_con_descuento} - total_con_descuento: {record.total_con_descuento}")

                record.margen_porcentaje_con_descuento = (
                            record.margen_con_descuento / record.total_con_descuento) if record.total_con_descuento else 0
            else:
                record.total_sin_descuento = 0
                record.margen_sin_descuento = 0
                record.margen_porcentaje_sin_descuento = 0
                record.precio_unit_dcto = 0
                record.total_con_descuento = 0
                record.margen_con_descuento = 0
                record.margen_porcentaje_con_descuento = 0


    @api.onchange("imprevisto", "qty")
    def _onchange_imprevisto(self):
        for record in self:
            if record.qty > 0:
                record._compute_costos_unitarios()
                record._compute_precios_venta()

