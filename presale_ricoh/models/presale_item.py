from odoo import models, fields, api

class PresaleOrderItem(models.Model):
    _name = 'presale.ricoh.order.item'
    _description = 'Presale Order Item'

    name = fields.Char(string="Nombre del Ítem", required=True)
    presale_order_id = fields.Many2one('presale.ricoh.order', string="Presale Order", ondelete="cascade")
    product_id = fields.Many2one('product.product', string="Producto", required=True,
                                 domain="[('es_impresora', '=', True)]")
    serie_id = fields.Many2one('stock.production.lot', string="Serie",
                              domain="[('product_id', '=', product_id), ('reservado_preventas', '=', False)]")
    qty = fields.Float(string="Cantidad", default=1.0)
    unit_price = fields.Float(string="Precio Unitario")

    item_detail_ids = fields.One2many('presale.ricoh.order.item.detail', 'item_id', string="Detalles del Ítem")

    dist = fields.Float(string="Precio", help="Precio especificado por el cliente")
    ld = fields.Float(string="LD", compute="_compute_ld", store=True, 
                     help="Precio * LD de configuracion")
    gm = fields.Float(string="GM", compute="_compute_gm", store=True,
                     help="LD / GM de configuracion")
    
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

    # totales o subtotales maquinas + accesorios
    subtotal_contrato = fields.Float(string="Subtotal", store=True, compute="_compute_subtotales_maquina",
                      help="Suma Total de Totales Maquina + Accesorios")
    
    subtotal_impuestos = fields.Float(string="Impuestos", store=True, compute="_compute_subtotales_maquina",
                      help="Suma Total de Exentos Maquina + Accesorios")
    
    total_contrato = fields.Float(string="Total a Pagar", store=True, compute="_compute_subtotales_maquina")

    total_cuota = fields.Float(string="Cuota", store=True, compute="_compute_subtotales_maquina")
    
    
    @api.depends('dist')
    def _compute_unit_price(self):
        """Calcula el precio unitario basado en el precio"""
        for record in self:
            record.unit_price = record.dist if record.dist else 0.0


    @api.depends('dist', 'presale_order_id.config_id.ld')
    def _compute_ld(self):
        """Calcula LD = dist * ld de configuración"""
        for record in self:
            if record.dist and record.presale_order_id.config_id.ld:
                record.ld = record.dist * record.presale_order_id.config_id.ld
            else:
                record.ld = 0.0


    @api.depends('ld', 'presale_order_id.config_id.gm')
    def _compute_gm(self):
        """Calcula GM = ld / gm de configuración"""
        for record in self:
            if record.ld and record.presale_order_id.config_id.gm:
                record.gm = record.ld / record.presale_order_id.config_id.gm
            else:
                record.gm = 0.0

    @api.depends('gm', 'presale_order_id.plazo_id.porcentaje')
    def _compute_intereses(self):
        """Calcula Intereses = gm * intereses de configuracion"""
        for record in self:
            if record.gm and record.presale_order_id.plazo_id.porcentaje:
                record.intereses = record.gm * record.presale_order_id.plazo_id.porcentaje 
            else:
                record.intereses = 0.0
    @api.depends('intereses', 'presale_order_id.config_id.iva', "qty")
    def _compute_iva(self):
        """Calcula IVA = intereses * iva de configuracion"""
        for record in self:
            if record.intereses and record.presale_order_id.config_id.iva:
                record.iva = record.intereses * record.presale_order_id.config_id.iva
                record.exen = record.iva / record.presale_order_id.config_id.iva
                record.subtotal_exen = record.exen * record.qty
                record.subtotal_iva = record.iva * record.qty
            else:
                record.iva = 0.0
                record.exen = 0.0

    @api.depends('iva', 'presale_order_id.plazo_id.plazo')
    def _compute_cuota(self):
        """Calcula Cuota = iva / plazo seleccionado"""
        for record in self:
            if record.iva and record.presale_order_id.plazo_id.plazo:
                record.cuota = record.iva / record.presale_order_id.plazo_id.plazo
            else:
                record.cuota = 0.0

    @api.depends(
        'subtotal_exen', 'subtotal_iva', 'iva', 'cuota',
        'item_detail_ids.subtotal_exen', 'item_detail_ids.subtotal_iva', 'item_detail_ids.iva', 'item_detail_ids.cuota', 'item_detail_ids.total'
    )
    def _compute_subtotales_maquina(self):
        """
        Calcula los totales y subtotales sumando los valores de la máquina y de los accesorios (detalles).
        """
        for record in self:
            # Sumar subtotales de los accesorios
            subtotal_exen_acc = sum(d.subtotal_exen for d in record.item_detail_ids)
            subtotal_iva_acc = sum(d.subtotal_iva for d in record.item_detail_ids)
            print("Sub total Exenta Accesorios", subtotal_exen_acc)
            print("Sub total iva Accesorios", subtotal_iva_acc)
            iva_acc = sum(d.iva for d in record.item_detail_ids)
            cuota_acc = sum(d.cuota for d in record.item_detail_ids)
            total_acc = sum(d.total for d in record.item_detail_ids)

            # Sumar los valores de la máquina (el propio record)
            subtotal_exen_maquina = record.subtotal_exen or 0.0
            subtotal_iva_maquina = record.subtotal_iva or 0.0
            print("Sub total Exenta Maquina", subtotal_exen_maquina)
            print("Sub total iva Maquina", subtotal_iva_maquina)

            exentas_totales_maq_acc = subtotal_exen_maquina + subtotal_exen_acc
            iva_totales_maq_acc = subtotal_iva_maquina + subtotal_iva_maquina
            
            impuestos_maq_acc = (exentas_totales_maq_acc * record.presale_order_id.config_id.iva) - exentas_totales_maq_acc
            print(f"Impuestos {exentas_totales_maq_acc} - {record.presale_order_id.config_id.iva} - {exentas_totales_maq_acc}")
            print(impuestos_maq_acc)
            total_pagar = exentas_totales_maq_acc + impuestos_maq_acc

            

            # Subtotal del contrato: suma de totales (maquina + accesorios)
            record.subtotal_contrato = exentas_totales_maq_acc
            # Subtotal de impuestos: suma de exentos (maquina + accesorios)
            record.subtotal_impuestos = impuestos_maq_acc
            # Total a pagar: suma de subtotales con IVA (maquina + accesorios)
            record.total_contrato = total_pagar
            # Total cuota: suma de cuotas (maquina + accesorios)
            record.total_cuota = total_pagar / record.presale_order_id.plazo_id.plazo

