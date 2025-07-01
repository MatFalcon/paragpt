from odoo import models, fields, api

class PresaleOrderItemDetail(models.Model):
    _name = 'presale.ricoh.order.item.detail'
    _description = 'Presale Order Item Detail Ricoh'

    name = fields.Char(string="Nombre del Detalle")
    item_id = fields.Many2one('presale.ricoh.order.item', string="Presale Item", ondelete="cascade")
    product_id = fields.Many2one('product.product', string="Producto",
                                 domain="[('es_accesorio', '=', True)]")
    serie_id = fields.Many2one('stock.production.lot', string="Serie", 
                              domain="[('product_id', '=', product_id), ('reservado_preventas', '=', False)]")
    qty = fields.Float(string="Cantidad", default=1.0)
    
    # Campos de precio
    dist = fields.Float(string="Precio", help="Precio especificado por el cliente")
    unit_price = fields.Float(string="Precio Unitario", compute="_compute_unit_price", store=True)
    
    # Campos calculados segun configuracion
    ld = fields.Float(string="LD", compute="_compute_ld", store=True, 
                     help="Precio Distribuidor * LD de configuración")
    gm = fields.Float(string="GM", compute="_compute_gm", store=True,
                     help="LD / GM de configuración")
    intereses = fields.Float(string="Intereses", compute="_compute_intereses", store=True,
                           help="GM * Intereses de configuración")
    iva = fields.Float(string="IVA", compute="_compute_iva", store=True,
                      help="Intereses * IVA de configuración")
    exen = fields.Float(string="S/iva", compute="_compute_iva", store=True,
                        help="Intereses / IVA de configuración * Cantidad")
    cuota = fields.Float(string="Cuota", compute="_compute_cuota", store=True,
                        help="IVA / Plazo seleccionado")    
    subtotal_exen = fields.Float(string="Subtotal Exenta", store=True, compute="_compute_iva",
                      help="Iva Unitario * Qty")
    subtotal_iva = fields.Float(string="Subtotal IVA", store=True, compute="_compute_iva",
                      help="Iva Unitario * Qty")


    # Campo total
    total = fields.Float(string="Total", compute="_compute_total", store=True)

    @api.depends('dist')
    def _compute_unit_price(self):
        """Calcula el precio unitario basado en el precio"""
        for record in self:
            record.unit_price = record.dist if record.dist else 0.0

    @api.depends('dist', 'item_id.presale_order_id.config_id.ld')
    def _compute_ld(self):
        """Calcula LD = dist * ld de configuracion"""
        for record in self:
            if record.dist and record.item_id.presale_order_id.config_id.ld:
                record.ld = record.dist * record.item_id.presale_order_id.config_id.ld
            else:
                record.ld = 0.0

    @api.depends('ld', 'item_id.presale_order_id.config_id.gm')
    def _compute_gm(self):
        """Calcula GM = ld / gm de configuracion"""
        for record in self:
            if record.ld and record.item_id.presale_order_id.config_id.gm:
                record.gm = record.ld / record.item_id.presale_order_id.config_id.gm
            else:
                record.gm = 0.0

    @api.depends('gm', 'item_id.presale_order_id.plazo_id.porcentaje')
    def _compute_intereses(self):
        """Calcula Intereses = gm * intereses de configuracion"""
        for record in self:
            if record.gm and record.item_id.presale_order_id.plazo_id.porcentaje:
                record.intereses = record.gm * record.item_id.presale_order_id.plazo_id.porcentaje 
            else:
                record.intereses = 0.0

    @api.depends('intereses', 'item_id.presale_order_id.config_id.iva')
    def _compute_iva(self):
        """Calcula IVA = intereses * iva de configuracion"""
        for record in self:
            if record.intereses and record.item_id.presale_order_id.config_id.iva:
                record.iva = record.intereses * record.item_id.presale_order_id.config_id.iva
                record.exen = record.iva / record.item_id.presale_order_id.config_id.iva
                record.subtotal_exen = record.exen * record.qty
                record.subtotal_iva = record.iva * record.qty
            else:
                record.iva = 0.0
                record.exen = 0.0

    @api.depends('iva', 'item_id.presale_order_id.plazo_id.plazo')
    def _compute_cuota(self):
        """Calcula Cuota = iva / plazo seleccionado"""
        for record in self:
            if record.iva and record.item_id.presale_order_id.plazo_id.plazo:
                record.cuota = record.iva / record.item_id.presale_order_id.plazo_id.plazo
            else:
                record.cuota = 0.0

    @api.depends('qty', 'unit_price')
    def _compute_total(self):
        """Calcula el total = cantidad * precio unitario"""
        for record in self:
            record.total = record.qty * record.unit_price if record.unit_price else 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Cuando se selecciona un producto, sugiere el precio"""
        if self.product_id:
            self.dist = self.product_id.list_price or 0.0

    # def _compute_calculos_variables(self):
    #     """
    #         Hace los calculos segun la planilla de preventas, este caso para los accesorios de la impresora cargada.
    #     """
    #     for record in self:
