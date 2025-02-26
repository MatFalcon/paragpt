from odoo import _, api, fields, models,exceptions

class NotasRemision(models.Model):
    _name = 'notas_remision_account.nota.remision'
    _inherit=['mail.thread','mail.activity.mixin']
    _description = 'Nota de remisión'
    _order = "name desc"

    name=fields.Char(string="Número",copy=False,default="Borrador",tracking=True)
    partner_id=fields.Many2one('res.partner',string="Cliente",tracking=True)
    state=fields.Selection(string="Estado",selection=[('draft','Borrador'),('posted','Publicado'),('cancel','Cancelado')],default='draft',copy=False,tracking=True)
    journal_id=fields.Many2one('account.journal',string="Diario",tracking=True)
    timbrado_id = fields.Many2one("interfaces_timbrado.timbrado", string="Timbrado", copy=False,tracking=True)
    company_id=fields.Many2one('res.company',string="Compañía",default=lambda self:self.env.company,tracking=True)
    motivo_traslado = fields.Selection(selection=[
        ('Venta a Facturar', 'Venta a Facturar'),
        ('Gentileza', 'Gentileza'),
        ('Garantía', 'Garantía'),
        ('Licitacion', 'Licitacion'),
    ], default='Venta a Facturar', string="Motivo de traslado", copy=False,tracking=True)
    invoice_id = fields.Many2one('account.move',string="Factura",copy=False,tracking=True)
    # comprobante_venta_nro = fields.Char(string="Comprobante de venta Nro.")
    nro_timbrado_comprobante = fields.Char(string="Timbrado de la factura",tracking=True)
    fecha_expedicion = fields.Date(string='Fecha de expedición',default=lambda self:fields.Date.today(),tracking=True)
    fecha_inicio_traslado = fields.Date(string='Fecha de inicio de traslado',tracking=True)
    fecha_fin_traslado = fields.Date(string='Fecha de fin de traslado',tracking=True)
    direccion_partida = fields.Char(string='Dirección de partida',
                                    default=lambda
                                        self: self.env.user.company_id.partner_id.street + self.env.user.company_id.partner_id.street2 if self.env.user.company_id.partner_id.street2 else ''
                                    ,tracking=True)
    direccion_entrega = fields.Char(string='Dirección de entrega',tracking=True)
    ciudad_partida = fields.Char(string="Ciudad de partida",
                                 default=lambda self: self.env.user.company_id.partner_id.city
                                 ,tracking=True)
    ciudad_entrega = fields.Char(string="Ciudad de entrega",tracking=True)
    departamento_partida = fields.Char(string="Departamento de partida",
                                       default=lambda
                                           self: self.env.user.company_id.partner_id.state_id.name
                                       ,tracking=True)
    departamento_entrega = fields.Char(string="Departamento de entrega",tracking=True)
    kms_recorridos = fields.Float(string="Kms estimados de recorrido",tracking=True)
    cambio = fields.Char(string="Cambio de fecha de término y/o Punto de traslado",tracking=True)
    motivo = fields.Char(string="Motivo del cambio",tracking=True)
    marca_vehiculo = fields.Char(string="Marca del vehículo de transporte",tracking=True)
    matricula = fields.Char(string="Matrícula",tracking=True)
    matricula_remolque = fields.Char(string="Matrícula remolque",tracking=True)
    transportista = fields.Char(string="Transportista",tracking=True)
    ruc_transportista = fields.Char(string="RUC del transportista",tracking=True)
    direccion_transportista = fields.Char(string="Dirección del transportista",tracking=True)
    chofer = fields.Char(string="Chofer",tracking=True)
    ruc_chofer = fields.Char(string="RUC o CI del chofer",tracking=True)
    direccion_chofer = fields.Char(string="Dirección del chofer",tracking=True)
    line_ids=fields.One2many('notas_remision_account.nota.remision.line','nota_id',string="Lineas de remisión")
    note=fields.Char(string="Observaciones")
    
    @api.onchange('partner_id')
    @api.depends('partner_id')
    def onchange_partner(self):
        self.invoice_id=False
        self.ciudad_entrega=self.partner_id.city_id.name if self.partner_id.city_id else False
        self.departamento_entrega=self.partner_id.state_id.name if self.partner_id.state_id else False

    @api.onchange('invoice_id')
    def onchange_partner(self):
        if self.invoice_id:
            if self.invoice_id.journal_id.timbrados_ids:
                timbrado_remision=self.invoice_id.journal_id.timbrados_ids.filtered(lambda x:x.tipo_documento=='nota_remision' and x.active)
                if timbrado_remision:
                    self.nro_timbrado_comprobante=timbrado_remision[0].name
                else:
                    self.nro_timbrado_comprobante=False
            else:
                self.nro_timbrado_comprobante=False
        else:
            self.nro_timbrado_comprobante=False
    

    def button_confirmar(self):
        for i in self:
            if not self.timbrado_id:
                raise exceptions.ValidationError('Se debe elegir un timbrado')
            vals={}
            if i.name and i.name == 'Borrador':
                secuencia=self.timbrado_id.journal_id.remision_sequence_id.next_by_id()
                vals['name']=secuencia
            vals['state']='posted'
            i.write(vals)
            if i.invoice_id:
                i.invoice_id.write({'nota_remision_id':i.id})
    
    def button_cancelar(self):
        for i in self:
            i.write({'state':'cancel'})
            if i.invoice_id:
                i.invoice_id.write({'nota_remision_id':False})

    def button_borrador(self):
        for i in self:
            i.write({'state':'draft'})
    def delete_lines(self):
        self.write({'line_ids':[(5,0,0)]})
        
    @api.onchange('invoice_id')
    def onchange_invoice(self):
        if self.invoice_id:
            self.action_cargar_productos()

    def action_cargar_productos(self):
        if not self.invoice_id:
            raise exceptions.ValidationError("Por favor seleccione una factura")
        self.delete_lines()
        new_lines=[]
        for line in self.invoice_id.invoice_line_ids:
            l={
                'product_id':line.product_id.id,
                'name':line.name,
                'qty':line.quantity,
                'uom_id':line.product_uom_id.id
            }
            new_lines.append((0,0,l))
        self.write({'line_ids':new_lines})

class NotasRemisionLine(models.Model):
    _name = 'notas_remision_account.nota.remision.line'
    _description = 'Línea de Nota de remisión'

    nota_id=fields.Many2one('notas_remision_account.nota.remision')
    product_code=fields.Char(string='Código')
    product_id=fields.Many2one('product.product',string='Producto')
    name=fields.Char(string='Descripción')
    qty=fields.Float(string='Cantidad')
    uom_id=fields.Many2one('uom.uom',string='U. medida')
    nro_lote_serie=fields.Char(string="Nro. Lote / Serie")