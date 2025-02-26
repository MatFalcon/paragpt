from odoo import api, fields, models, exceptions


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name,timbrado_id)',
         'No se puede duplicar el número de nota de remisión en el mismo timbrado')
    ]

    motivo_traslado = fields.Selection(selection=[
        ('Venta a Facturar', 'Venta a Facturar'),
        ('Gentileza', 'Gentileza'),
        ('Garantía', 'Garantía'),
        ('Licitacion', 'Licitacion'),
    ], default='Venta a Facturar', string="Motivo de traslado", copy=False)
    comprobante_venta = fields.Char(string="Comprobante de venta")
    comprobante_venta_nro = fields.Char(string="Comprobante de venta Nro.")
    nro_timbrado_comprobante = fields.Char(string="Timbrado")
    fecha_expedicion = fields.Date(string='Fecha de expedición')
    fecha_inicio_traslado = fields.Date(string='Fecha de inicio de traslado')
    fecha_fin_traslado = fields.Date(string='Fecha de fin de traslado')
    direccion_partida = fields.Char(string='Dirección de partida',
                                    default=lambda
                                        self: self.env.user.company_id.partner_id.street + self.env.user.company_id.partner_id.street2 if self.env.user.company_id.partner_id.street2 else ''
                                    )
    direccion_entrega = fields.Char(string='Dirección de entrega')
    ciudad_partida = fields.Char(string="Ciudad de partida",
                                 default=lambda self: self.env.user.company_id.partner_id.city
                                 )
    ciudad_entrega = fields.Char(string="Ciudad de entrega")
    departamento_partida = fields.Char(string="Departamento de partida",
                                       default=lambda
                                           self: self.env.user.company_id.partner_id.state_id.name
                                       )
    departamento_entrega = fields.Char(string="Departamento de entrega")
    kms_recorridos = fields.Float(string="Kms estimados de recorrido")
    cambio = fields.Char(string="Cambio de fecha de término y/o Punto de traslado")
    motivo = fields.Char(string="Motivo")
    marca_vehiculo = fields.Char(string="Marca del vehículo de transporte")
    matricula = fields.Char(string="Matrícula")
    matricula_remolque = fields.Char(string="Matrícula remolque")
    transportista = fields.Char(string="Transportista")
    ruc_transportista = fields.Char(string="RUC del transportista")
    direccion_transportista = fields.Char(string="Dirección del transportista")
    chofer = fields.Char(string="Chofer")
    ruc_chofer = fields.Char(string="RUC o CI del chofer")
    direccion_chofer = fields.Char(string="Dirección del chofer")
    timbrado_id = fields.Many2one("interfaces_timbrado.timbrado", string="Timbrado", copy=False)
    es_nota_remision = fields.Boolean(string="Es nota de remision", default=False, compute="compute_nota_remision")
    move_name = fields.Char(string="Nro. de remision", copy=False)

    @api.onchange('picking_type_id', 'partner_id')
    @api.depends('picking_type_id', 'partner_id')
    def onchange_picking_type_id_2(self):
        for r in self:
            if r.picking_type_id.code == 'outgoing':
                r.direccion_partida = ''
                if self.env.user.company_id.partner_id.street:
                    r.direccion_partida = self.env.user.company_id.partner_id.street
                if self.env.user.company_id.partner_id.street2:
                    r.direccion_partida += ' '
                    r.direccion_partida += self.env.user.company_id.partner_id.street2
                if self.env.user.company_id.partner_id.city:
                    r.ciudad_partida = self.env.user.company_id.partner_id.city
                if self.env.user.company_id.partner_id.state_id:
                    r.departamento_partida = self.env.user.company_id.partner_id.state_id.name

                r.direccion_entrega = ''
                r.ciudad_entrega = ''
                r.departamento_entrega = ''
                if r.partner_id and r.partner_id.child_ids:
                    for i in r.partner_id.child_ids:
                        if i.type == 'delivery':
                            if i.street:
                                r.direccion_entrega = i.street
                            if i.street2:
                                r.direccion_entrega += ' '
                                r.direccion_entrega += i.street2
                            if i.city:
                                r.ciudad_entrega = i.city
                            if i.state_id:
                                r.departamento_entrega = i.state_id.name

    @api.depends('picking_type_id')
    def compute_nota_remision(self):
        for i in self:
            if i.picking_type_id.nota_remision:
                i.es_nota_remision = True
            else:
                i.es_nota_remision = False

    def obtener_nombre(self):
        if not self.timbrado_id or not self.timbrado_id.journal_id or not self.timbrado_id.journal_id.remision_sequence_id:
            raise exceptions.ValidationError(
                'No se encuentra un timbrado para esta nota. Favor verificar el Diario o Timbrado')
        return self.timbrado_id.journal_id.remision_sequence_id.sudo().next_by_id()

    def button_validate(self):
        for i in self:
            res = super(StockPicking, i).button_validate()
            if i.timbrado_id and not i.move_name:
                nuevo_nombre = i.obtener_nombre()
                i.write({'name': nuevo_nombre, 'move_name': nuevo_nombre})
            return res


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    nota_remision = fields.Boolean("Es una operación de nota de remisión", default=False, copy=False)
    seleccion = fields.Boolean("Es una operación de selección", default=False, copy=False)

    @api.onchange('code')
    @api.depends('code')
    def onchange_code(self):
        for i in self:
            if i.code != 'outgoing':
                i.nota_remision = False
