from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree
import logging
_logger = logging.getLogger(__name__)

class PresaleOrder(models.Model):
    _name = 'presale.ricoh.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Presale Order'

    name = fields.Char(string='Nombre del Pedido', required=True)
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    lead_id = fields.Many2one('crm.lead', string='Oportunidad')
    date_order = fields.Datetime(string='Fecha del Pedido', default=fields.Datetime.now)
    
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('solicitud_aprobacion', 'Solicitud de Aprobación'),
        ('en_revision', 'En Revisión'),
        ('confirmado', 'Confirmado'),
        ('aprobado', 'Aprobado'),
        ('analisis_credito', 'Análisis de Crédito'),
        ('rechazado', 'Rechazado'),
    ], string='Estado', default='borrador', tracking=True)
    
    commercials_ids = fields.Many2one(
        'res.users',
        string='Comercial'
    )
    crear_presupuesto = fields.Boolean(string="Crear Presupuesto", default=True)
    presupuesto_id = fields.Many2one('sale.order', string="Presupuesto de Venta")
    equipo_de_venta = fields.Char(string="Equipo de Venta")
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento")
    forma_pago = fields.Char(string="Forma de Pago")
    condiciones_pago = fields.Text(string="Condiciones de Pago")
    
    # Totales
    subtotal_contrato = fields.Float(string="Subtotal", compute="_compute_totales_contrato", store=True)
    subtotal_impuestos = fields.Float(string="Impuestos", compute="_compute_totales_contrato", store=True)
    total_contrato = fields.Float(string="Total a Pagar", compute="_compute_totales_contrato", store=True)
    total_cuota = fields.Float(string="Cuota", compute="_compute_totales_contrato", store=True)
    order_item_ids = fields.One2many('presale.ricoh.order.item', 'presale_order_id', string="Líneas del Pedido")

    # Campos de relacion con configuraciones
    config_id = fields.Many2one('presale.ricoh.config', string='Configuración', 
                               default=lambda self: self._get_default_config())
    plazo_id = fields.Many2one('presale.ricoh.intereses', string='Plazo de Interés',
                              default=lambda self: self._get_default_plazo())

    # Variables editables que se toman desde la configuracion
    # Se mantienen como related=False para permitir edición manual, con store=True
    ld = fields.Float(string='LD', related='config_id.ld', readonly=False, store=True)
    gm = fields.Float(string='GM', related='config_id.gm', readonly=False, store=True)
    intereses = fields.Float(string='Intereses', related='plazo_id.porcentaje', readonly=False, store=True)
    iva = fields.Float(string='IVA', related='config_id.iva', readonly=False, store=True)


    descuento_comercial = fields.Float(
        string='Descuento Comercial (%)', 
        default=0.0,
        help='Descuento que puede aplicar el comercial (máximo 15% del margen GM)'
    )
    
    descuento_solicitado = fields.Float(
        string='Descuento Solicitado (%)', 
        default=0.0,
        help='Descuento adicional solicitado al supervisor'
    )
    
    descuento_aprobado = fields.Float(
        string='Descuento Aprobado (%)', 
        default=0.0,
        help='Descuento final aprobado por el supervisor'
    )
    
    descuento_total = fields.Float(
        string='Descuento Total (%)',
        compute='_compute_descuento_total',
        store=True,
        help='Descuento total aplicado (comercial + aprobado)'
    )
    
    requiere_aprobacion = fields.Boolean(
        string='Requiere Aprobación',
        compute='_compute_requiere_aprobacion',
        store=True,
        help='Se activa cuando el descuento supera el 15% del margen'
    )
    
    motivo_descuento = fields.Text(
        string='Motivo del Descuento',
        help='Justificación para el descuento solicitado'
    )
    
    fecha_solicitud_aprobacion = fields.Datetime(
        string='Fecha Solicitud Aprobación',
        readonly=True
    )
    
    aprobado_por = fields.Many2one(
        'res.users',
        string='Aprobado Por',
        readonly=True
    )
    
    fecha_aprobacion = fields.Datetime(
        string='Fecha Aprobación',
        readonly=True
    )
    
    comentarios_supervisor = fields.Text(
        string='Comentarios del Supervisor'
    )

    
    @api.depends('descuento_comercial', 'descuento_aprobado')
    def _compute_descuento_total(self):
        for record in self:
            record.descuento_total = record.descuento_comercial + record.descuento_aprobado
    
    @api.depends('descuento_comercial', 'gm')
    def _compute_requiere_aprobacion(self):
        for record in self:
            if record.gm > 0:
                limite_descuento = record.gm * 0.15
                record.requiere_aprobacion = record.descuento_comercial > limite_descuento
            else:
                record.requiere_aprobacion = False


    @api.model
    def _get_default_config(self):
        config = self.env['presale.ricoh.config'].search([], limit=1)
        return config.id if config else False

    @api.model
    def _get_default_plazo(self):
        plazo = self.env['presale.ricoh.intereses'].search([], limit=1)
        return plazo.id if plazo else False

    @api.onchange('config_id')
    def _onchange_config_id(self):
        if self.config_id:
            self.ld = self.config_id.ld
            self.gm = self.config_id.gm
            self.iva = self.config_id.iva

    @api.onchange('plazo_id')
    def _onchange_plazo_id(self):
        if self.plazo_id:
            self.intereses = self.plazo_id.porcentaje

    @api.depends('order_item_ids.subtotal_contrato', 'order_item_ids.subtotal_impuestos', 
                 'order_item_ids.total_contrato', 'order_item_ids.total_cuota')
    def _compute_totales_contrato(self):
        for order in self:
            order.subtotal_contrato = sum(line.subtotal_contrato for line in order.order_item_ids)
            order.subtotal_impuestos = sum(line.subtotal_impuestos for line in order.order_item_ids)
            order.total_contrato = sum(line.total_contrato for line in order.order_item_ids)
            order.total_cuota = sum(line.total_cuota for line in order.order_item_ids)

 
    @api.constrains('descuento_comercial', 'gm')
    def _check_descuento_comercial(self):
        for record in self:
            if record.descuento_comercial < 0:
                raise ValidationError(_("El descuento comercial no puede ser negativo."))
            
            # Solo validar límite si el usuario no es administrador
            if not self.env.user.has_group('presale_ricoh.group_presale_ricoh_manager'):
                if record.gm > 0:
                    limite_descuento = record.gm * 0.15
                    if record.descuento_comercial > limite_descuento:
                        raise ValidationError(_(
                            "El descuento comercial no puede superar el 15%% del margen GM.\n"
                            "Límite permitido: %.2f%%\n"
                            "Descuento ingresado: %.2f%%"
                        ) % (limite_descuento, record.descuento_comercial))


    def action_solicitar_aprobacion(self):
        """Solicita aprobación para descuentos superiores al límite"""
        for record in self:
            if record.state != 'borrador':
                raise UserError(_("La preventa debe estar en estado 'Borrador' para solicitar aprobación."))
            
            if not record.requiere_aprobacion:
                raise UserError(_("Esta preventa no requiere aprobación de descuento."))
            
            if not record.motivo_descuento:
                raise UserError(_("Debe especificar el motivo del descuento antes de solicitar aprobación."))
            
            record.write({
                'state': 'solicitud_aprobacion',
                'fecha_solicitud_aprobacion': fields.Datetime.now(),
            })
            
            self._notify_supervisors()
    
    def action_pasar_revision(self):
        """El supervisor toma la solicitud para revisión"""
        for record in self:
            if record.state != 'solicitud_aprobacion':
                raise UserError(_("Solo se pueden revisar preventas en estado 'Solicitud de Aprobación'."))
            
            if not self.env.user.has_group('presale_ricoh.group_presale_ricoh_manager'):
                raise UserError(_("No tiene permisos para revisar solicitudes de descuento."))
            
            record.state = 'en_revision'
    
    def action_aprobar_descuento(self):
        """Aprueba el descuento solicitado"""
        for record in self:
            if record.state != 'en_revision':
                raise UserError(_("Solo se pueden aprobar preventas en estado 'En Revisión'."))
            
            if not self.env.user.has_group('presale_ricoh.group_presale_ricoh_manager'):
                raise UserError(_("No tiene permisos para aprobar descuentos."))
            
            record.write({
                'state': 'confirmado',
                'descuento_aprobado': record.descuento_solicitado,
                'aprobado_por': self.env.user.id,
                'fecha_aprobacion': fields.Datetime.now(),
                'comentarios_supervisor': self.comentarios_supervisor, # Asegura que se guardan los comentarios del supervisor al aprobar
            })
    
    def action_rechazar_descuento(self):
        """Rechaza el descuento solicitado"""
        for record in self:
            if record.state not in ['solicitud_aprobacion', 'en_revision']:
                raise UserError(_("Solo se pueden rechazar preventas en solicitud de aprobación o en revisión."))
            
            if not self.env.user.has_group('presale_ricoh.group_presale_ricoh_manager'):
                raise UserError(_("No tiene permisos para rechazar descuentos."))
            
            record.write({
                'state': 'rechazado',
                'descuento_solicitado': 0.0,
                'descuento_aprobado': 0.0,
                'motivo_descuento': '', # Limpiar motivo ya que fue rechazado
                'fecha_solicitud_aprobacion': False,
            })
    
    def action_confirm(self):
        """Confirma la preventa (desde borrador, si no requiere aprobación)"""
        for record in self:
            if record.state != 'borrador':
                raise UserError(_("Solo se pueden confirmar preventas en estado 'Borrador'."))
            
            if record.requiere_aprobacion:
                raise UserError(_("Esta preventa requiere aprobación de descuento. Use 'Solicitar Aprobación'."))
            
            record.state = 'confirmado'

    def action_approve(self):
        """Aprueba la preventa y genera/actualiza presupuesto"""
        for order in self:
            if order.state != 'confirmado':
                raise UserError(_("Solo se pueden aprobar preventas confirmadas."))
            
            if order.crear_presupuesto:
                if not order.presupuesto_id:
                    unit = self.env['operating.unit'].search([('code', '=', 'RCH')], limit=1) 
                    if not unit:
                        raise UserError(_("No se encontró la unidad operativa 'RCH'."))

                    nuevo_presupuesto = self.env['sale.order'].create({
                        'partner_id': order.partner_id.id,
                        'origin': order.name,
                        'opportunity_id':order.lead_id.id,
                        'currency_id': order.lead_id.company_currency,
                        'presale_ricoh_id': order.id,
                        #'operating_unit ': unit.id,
                        'date_order': order.date_order,
                        'validity_date': order.fecha_vencimiento,
                        'payment_term_id': self._get_payment_term(order.forma_pago) if order.forma_pago else False,
                        'note': order.condiciones_pago or '',
                    })
                    order.presupuesto_id = nuevo_presupuesto.id
                    print("Se crea el presupuesto", nuevo_presupuesto)
                    self._generate_sale_order_lines(order, nuevo_presupuesto)
                    print("Presupuesto en Cotizador", order.presupuesto_id)
                    order.state = 'aprobado' 
                    
                else:
                    if order.presupuesto_id.state == 'draft':
                        if not self.env.context.get('update_confirmed', False):
                            return {
                                'name': _('Actualizar Orden de Venta'),
                                'type': 'ir.actions.act_window',
                                'res_model': 'presale.update.wizard',
                                'view_mode': 'form',
                                'target': 'new',
                                'context': {'default_presale_id': order.id},
                            }
                        else:
                            order.presupuesto_id.write({
                                'partner_id': order.partner_id.id,
                                'origin': order.name,
                                'opportunity_id':order.lead_id.id,
                                'operating_unit':unit.id,
                                'date_order': order.date_order,
                                'validity_date': order.fecha_vencimiento,
                                'payment_term_id': self._get_payment_term(order.forma_pago) if order.forma_pago else False,
                                'note': order.condiciones_pago or '',
                            })
                            
                            order.presupuesto_id.order_line.unlink()
                            self._generate_sale_order_lines(order, order.presupuesto_id)
                            order.state = 'aprobado' # Transición a aprobado después de actualizar presupuesto
                    else:
                        raise UserError(_("La Orden de Venta ya no está en borrador y no puede ser actualizada."))

            if order.state == 'aprobado' and order.presupuesto_id:
                # Transición a 'analisis_credito' si el presupuesto existe y la preventa está aprobada
                order.state = 'analisis_credito'
        return True


    def action_volver_borrador(self):
        """Permite volver al estado borrador (solo administradores)"""
        if not self.env.user.has_group('presale_ricoh.group_presale_ricoh_manager'):
            raise UserError(_("No tiene permisos para volver al estado borrador."))
        
        for record in self:
            record.write({
                'state': 'borrador',
                'descuento_solicitado': 0.0,
                'descuento_aprobado': 0.0,
                'fecha_solicitud_aprobacion': False,
                'aprobado_por': False,
                'fecha_aprobacion': False,
                'comentarios_supervisor': '',
                'motivo_descuento': '',
            })

    
    def _notify_supervisors(self):
        supervisors = self.env['res.users'].sudo().search([
            ('groups_id', 'in', self.env.ref('presale_ricoh.group_presale_ricoh_manager').id)
        ])
        
        for supervisor in supervisors:
            
            self.message_post(
                body=_("Solicitud de aprobación de descuento del %.2f%% por %s para preventa <a href='/web#id=%s&view_type=form&model=presale.ricoh.order'>%s</a>. Motivo: %s") % (
                    self.descuento_comercial, self.commercials_ids.name, self.id, self.name, self.motivo_descuento
                ),
                partner_ids=[supervisor.partner_id.id],
                subtype_xmlid='mail.mt_note'
            )


    def action_view_lead(self):
        self.ensure_one()
        if not self.lead_id:
            raise UserError(_("No hay una oportunidad asociada a esta preventa."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Oportunidad'),
            'res_model': 'crm.lead',
            'res_id': self.lead_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'context': {'default_type': 'opportunity'}
        }

    def action_view_sale_order(self):
        self.ensure_one()
        if not self.presupuesto_id:
            raise UserError(_("No hay un presupuesto asociado a esta preventa."))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Presupuesto'),
            'res_model': 'sale.order',
            'res_id': self.presupuesto_id.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for rec in self.env.user.operating_unit_ids:
            if not self.env.user.has_group('crm_technoma.group_segmentacion_res_partner') and rec.name == 'RICOH':
                return {
                    'domain': {
                        'partner_id': ['|', ('user_id', '=', self.env.user.id), ('user_id', '=', False)]
                    }
                }
        
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PresaleOrder, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='partner_id']"):
                for rec in self.env.user.operating_unit_ids:
                    if not self.env.user.has_group('crm_technoma.group_segmentacion_res_partner') and rec.name == 'RICOH':
                        node.set('options', '{"no_create": true, "no_create_edit": true}')
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    
    def _generate_sale_order_lines(self, presale_order, sale_order):
        """Genera las líneas de la orden de venta basándose en los items y detalles de la preventa"""
        sequence = 10
        
        for item in presale_order.order_item_ids:
            sale_line_vals = self._prepare_sale_order_line_vals(
                item, sale_order, sequence, is_accessory=False
            )
            
            self.env['sale.order.line'].create(sale_line_vals)
            
            if item.serie_id:
                item.serie_id.write({'reservado_preventas': True})
            
            sequence += 10
            
            for detail in item.item_detail_ids:
                accessory_line_vals = self._prepare_sale_order_line_vals(
                    detail, sale_order, sequence, is_accessory=True, parent_item=item
                )
                
                self.env['sale.order.line'].create(accessory_line_vals)
                
                if detail.serie_id:
                    detail.serie_id.write({'reservado_preventas': True})
                
                sequence += 10

    def _prepare_sale_order_line_vals(self, line_item, sale_order, sequence, is_accessory=False, parent_item=None):
        product = line_item.product_id
        name = line_item.product_id.name
        
        if is_accessory:
            name = f"{name}" #Accesorio
            price_unit = line_item.iva
        else:
            price_unit = line_item.iva # El precio unitario de la línea es el IVA calculado
        
        if line_item.serie_id:
            name += f"{line_item.serie_id.name}"
        
        qty = line_item.qty
        
        taxes = product.taxes_id.filtered(lambda t: t.company_id == sale_order.company_id)
        
        vals = {
            'order_id': sale_order.id,
            'product_id': product.id,
            'name': name,
            'product_uom_qty': qty,
            'product_uom': product.uom_id.id,
            'price_unit': price_unit,
            'tax_id': [(6, 0, taxes.ids)] if taxes else False,
            'sequence': sequence,
            'presale_item_id': line_item.id if not is_accessory else False,
            'presale_detail_id': line_item.id if is_accessory else False,
        }
        
        return vals

    def _get_payment_term(self, forma_pago):
        if not forma_pago:
            return False
        
        payment_term = self.env['account.payment.term'].search([
            ('name', 'ilike', forma_pago)
        ], limit=1)
        
        if payment_term:
            return payment_term.id
        
        default_term = self.env['account.payment.term'].search([], limit=1)
        return default_term.id if default_term else False

class PresaleUpdateWizard(models.TransientModel):
    _name = 'presale.update.wizard'
    _description = 'Wizard para actualizar la Orden de Venta desde la Preventa'

    presale_id = fields.Many2one('presale.ricoh.order', string="Preventa", required=True)

    def action_confirm_update(self):
        return self.presale_id.with_context(update_confirmed=True).action_approve()

    def action_cancel_update(self):
        return {'type': 'ir.actions.act_window_close'}