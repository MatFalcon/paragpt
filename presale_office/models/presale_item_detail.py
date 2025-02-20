# -*- coding: utf-8 -*-

from odoo import fields, models, exceptions, api , _





class PreSaleOrderItem(models.Model):
    _name = 'presale.order.item.detail'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", copy=True)
    headling_id = fields.Many2one('presale.order.heading', store=True, copy=True)
    item_id = fields.Many2one('presale.order.item', copy=True)
    order_id = fields.Many2one(related='headling_id.order_id',store=True, copy=True)
    code = fields.Char(string="Code", copy=True)
    description = fields.Char(string="Description", tracking=True, copy=True)
    product_id = fields.Many2one('product.product',string="Product", tracking=True, copy=True)
    unit_price = fields.Float(string="Unit Mat.",tracking=True, copy=True)
    ############ Calculos Preventa ############
    qty = fields.Integer(string="Quantity", tracking=True, copy=True, default=1)
    uom_id = fields.Many2one('uom.uom',string="Uom", tracking=True, copy=True)
    standard_price = fields.Float(string="Cost")
    # ------ Calculo Unitario -----
    margen_venta = fields.Float(string="Margen", default=2.42, readonly=True)
    porcentaje_descuento = fields.Float(string="Descuento", default=0.1, readonly=True)# 10%


    # ----- Calculo Totales  y Calculo de Margenes -----
    total_cost = fields.Float(string="Costos Totales", compute="_compute_costo")
    total_sin_descuento = fields.Float(string="Total Sin Descuento")




    price_subtotal = fields.Float(string="Subtotal Mat.",  store=True, copy=True)

    materiales = fields.Float(string="Materiales", tracking=True, copy=True)
    mano_obra = fields.Float(string="Mano de Obra", tracking=True, copy=True)
    unit_cost = fields.Float(string="Costo Unitario",tracking=True, copy=True, compute="calculate_presale_factors")
    total_qty = fields.Float(string="Cantidad Total",tracking=True, copy=True, compute="calculate_presale_factors")
    supplier_id = fields.Many2one('res.partner','Supplier', tracking=True, copy=True)
    account_analytic_id = fields.Many2many('account.account.tag', string="Etiquetas Analíticas", required=True, tracking=True, copy=True)
    product_seller_list = fields.One2many(related="product_id.seller_ids", string="Supplier Prices", readonly=True)

    @api.depends("product_id", "standard_price", "qty")
    def _compute_costo(self):
        for record in self:
            if record.qty:
                record.total_cost = record.standard_price * record.qty
            else:
                record.total_cost = 0

    @api.onchange("product_id", "qty")
    def onchange_product_id(self):
        for rec in self:
            # setear el precio de costo y totales
            rec.standard_price = rec.product_id.product_tmpl_id.standard_price
            if rec.qty != 0:
                rec.total_cost = rec.standard_price * rec.qty
            else:
                rec.total_cost = rec.standard_price


    @api.depends('gastos_porcentaje_10', 'gastos_porcentaje_20', 'unit_cost')
    def calcular_gastos_administrativos(self):
        self.gastos_def_10 = 0
        self.unit_cost_total = 0
        self.gastos_def_20 = 0
        self.total_cost = 0
        for r in self:
            r.gastos_def_10 = (r.gastos_porcentaje_10 * r.unit_cost) / 100
            r.gastos_def_20 = (r.gastos_porcentaje_20 * r.unit_cost) / 100
            r.unit_cost_total = r.gastos_def_20 + r.gastos_def_10 + r.unit_cost


    @api.onchange('product_id')
    def set_product_uom(self):
        for rec in self:
            if rec.product_id:
                rec.uom_id = rec.product_id.uom_id.id
            else:
                rec.uom_id = None

    @api.depends('unit_price', 'qty', 'total_qty', 'headling_id.item_id', 'materiales', 'mano_obra', 'product_id')
    def calculate_presale_factors(self):
        for rec in self:
            if rec.mano_obra > 0 or rec.materiales > 0:
                rec.unit_cost = rec.materiales + rec.mano_obra

                # Asegurarse de que rec.order_id es una relación de muchos a uno o muchos
                if rec.order_id:
                    # Verificar si algún producto coincide con el product_id del registro
                    matching_products = rec.order_id.filtered(lambda p: p.product_id == rec.product_id)
                    # Inicializar total_qty con 0 para empezar la acumulación
                    rec.total_qty = 0
                    if matching_products:
                        # Acumular las cantidades de las líneas coincidentes
                        for product in matching_products:
                            rec.total_qty += product.qty
                    else:
                        rec.total_qty += rec.qty if rec.qty > 0 else 0
                else:
                    rec.total_qty = rec.qty if rec.qty > 0 else 0

            else:
                rec.unit_cost = 0
                rec.unit_price = 0
                rec.total_qty = 0


