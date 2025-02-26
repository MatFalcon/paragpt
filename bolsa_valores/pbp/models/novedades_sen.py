# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, api
import re
from odoo.addons.pbp.facturas.generador import generar_facturas
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class NovedadesSEN(models.Model):
    _name = 'pbp.novedades_sen'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    emisor_descripcion = fields.Char(required=True, string='Emisor Descripción')
    emisor_id = fields.Integer(required=True)
    cod_negociacion = fields.Char(required=True, string='Cód. Negociación')
    tipo_contrato_descripcion = fields.Char(required=True, string='Tipo Contrato Descripción')
    tipo_contrato_codigo = fields.Char(required=True, string='Tipo Contrato Código')
    contrato_descripcion = fields.Char(required=True, string='Contrato Descripción')
    contrato_id = fields.Integer(required=True)
    persona_id = fields.Integer(required=True)
    instrumento = fields.Char(required=True)
    fecha_emision = fields.Date(string='Fecha de Emisión')
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento')
    monto_emitido = fields.Float(required=True)
    cantidad_emitida = fields.Integer(required=True)

    state = fields.Selection(selection=[
       ('draft', 'Draft'),
       ('in_progress', 'In Progress'),
       ('cancel', 'Cancelled'),
       ('done', 'Done'),
   ], string='Status', required=True, readonly=True, copy=False,
   tracking=True, default='draft')

    partner_id = fields.Many2one('res.partner', string="Cliente")
    currency_id = fields.Many2one('res.currency', required=True, string="Moneda")
    product_id = fields.Many2one('product.product', string='Producto')
    invoice_id = fields.Many2one('account.move', string='Factura')

    #campos de emision y custodia que se pasan a sen
    fecha_reporte = fields.Date(string="Fecha de reporte", compute="_compute_fecha_reporte", store=True)


    # Custodia
    product_custodia_id = fields.Many2one('product.product', string="Producto custodia", domain=[('es_custodia', '=', True)])
    custodia_tasa_arancel = fields.Float(string="Tasa Arancel Custodia", digits=(16, 4), compute="_compute_obtener_arancel_tasa_custodia", store=True)
    custodia_arancel = fields.Monetary(string="Arancel Custodia", compute="_compute_arancel_custodia_pyg", store=True)
    custodia_iva = fields.Monetary(string="IVA Custodia", compute="_compute_custodia_arancel_iva", store=True)
    custodia_arancel_pyg = fields.Monetary(string="Arancel Custodia en PYG", compute="_custodia_arancel_pyg", store=True)
    custodia_total = fields.Monetary(string="Total Custodia", compute="_compute_custodia_total", store=True)

    # Emision
    product_emision_id = fields.Many2one('product.product', string="Producto emision")
    emision_tasa_arancel = fields.Float(string="Tasa Arancel Emisión", digits=(16, 4), compute="_compute_obtener_arancel_emision", store=True)
    emision_arancel = fields.Monetary(string="Arancel Emisión", compute="_compute_arancel_custodia_pyg", store=True)
    emision_iva = fields.Monetary(string="IVA Emisión", compute="_compute_emision_iva", store=True)
    emision_arancel_pyg = fields.Monetary(string="Arancel Emisión en PYG")
    emision_total = fields.Monetary(string="Total Emisión", compute="_compute_emision_total", store=True)
    
    total_emision_custodia = fields.Monetary(string="Total Emisión y Custodia", compute="_compute_total_emision_custodia", store=True)
    total_emision_custodia_pyg = fields.Monetary(string="Total Emisión y Custodia en PYG")

    #campos de la sincronizacion que era de series
    cod_emisor = fields.Char(string='Código Emisor')
    monto_original = fields.Float(string='Monto Original')
    inicio_colocacion = fields.Date(string='Inicio Colocación')
    fecha_vencimiento_emision = fields.Date(string='Fecha Vencimiento del titulo emitido')
    instrumento_emi = fields.Char()
    instrumento_emision = fields.Char(string='Instrumento del Titulo Emitido', compute="_compute_instrumento", store=True)
    tasa_instrumento = fields.Float(string='Tasa Instrumento')
    monto_pyg = fields.Monetary(string="Monto en PYG", compute="_compute_monto_original", store=True)
    dias_reporte = fields.Integer(string="Días de reporte", compute="_compute_dias_reporte", store=True)
    monto_moneda_original = fields.Monetary(string="Monto en moneda original")
    # currency_id = fields.Many2one('res.currency', string='Moneda')
    # partner_id = fields.Many2one('res.partner', string='Partner')

    # Campos para calcular
    monto_custodiado = fields.Float(compute='_compute_monto_custodiado', store=True)    
    fecha_inicial = fields.Date(default=lambda: datetime.date(datetime.datetime.now().year, 1, 1))
    plazo_emision = fields.Integer(compute='_compute_plazo_emision', store=True)
    plazo_por_titulo = fields.Integer(compute='_compute_plazo_por_titulo', store=True)
    arancel_anual = fields.Float(compute='_compute_arancel_anual', store=True)
    custodia_diaria = fields.Float(compute='_compute_custodia_diaria', store=True)
    arancel_custodia = fields.Float(compute='_compute_arancel_custodia', store=True)
    iva_custodia = fields.Float(compute='_compute_iva_custodia', store=True)
    total_custodia = fields.Float(compute='_compute_total_custodia', store=True)

    name = fields.Char(string="Name", compute="_compute_name", store=True)
    resolucion_id = fields.Many2one('resolucion', string='Resolución', tracking=True)  
    tc_cierre_mes = fields.Float(string="TC del día", compute="_compute_currency_id", store=True)

    @api.depends('fecha_vencimiento')
    def _compute_plazo_emision(self):
        for record in self:
            if record.fecha_vencimiento:
                # Obtener el año corriente
                year_actual = datetime.datetime.now().year
                # Crear la fecha inicial del año corriente
                fecha_inicial_anho_actual = datetime.date(year_actual, 1, 1)
                # Calcular el plazo
                if record.fecha_vencimiento.year == year_actual:
                    record.plazo_emision = (record.fecha_vencimiento - fecha_inicial_anho_actual).days + 1
                else:
                    record.plazo_emision = 0
            else:
                record.plazo_emision = 0

    @api.depends('fecha_vencimiento','inicio_colocacion')
    def _compute_plazo_por_titulo(self):
        for record in self:
            if record.fecha_vencimiento:
                # Calcular el plazo
                record.plazo_por_titulo = (record.fecha_vencimiento - record.inicio_colocacion).days
           
            else:
                record.plazo_por_titulo = 0

    #onchange para el producto de emision y custodia
    @api.depends('instrumento')
    def _compute_instrumento(self):
        if self.instrumento == 'Bono Financiero' or self.instrumento == "Bono" or self.instrumento == "bono":
            self.product_custodia_id = 165
            self.product_emision_id = 157
            self.instrumento_emision = self.instrumento
        else:
            self.product_custodia_id = False
            self.product_emision_id = 158
            self.instrumento_emision = self.instrumento

    #onchange para el titulo del registro
    @api.depends('partner_id', 'cod_negociacion')
    def _compute_name(self):
        for record in self:
            partner_name = record.partner_id.name if record.partner_id else 'No Partner'
            cod_negociacion = record.cod_negociacion or 'No Code'
            record.name = f'{partner_name} / {cod_negociacion}'

    #onchange para la fecha de reporte (el ultimo dia del año corriente)
    @api.depends('cod_negociacion')
    def _compute_fecha_reporte(self):
        for i in self:
            date = datetime.date.today()
            year = date.year
            fecha_reporte = '31/12/'+ str(year)
            i.fecha_reporte = datetime.datetime.strptime(fecha_reporte, '%d/%m/%Y')

    @api.depends('instrumento_emision')
    def _compute_obtener_arancel_tasa_custodia(self):
        if self.instrumento_emision.lower() == "bono" or re.search(r'\bbono\b', self.instrumento_emision, re.IGNORECASE):

            self.custodia_tasa_arancel = 0.0001
        else:
            self.custodia_tasa_arancel = 0
    

    #OBTENER CALCULOS COLUMNA EMISION
    @api.depends('instrumento_emision', 'plazo_por_titulo', 'monto_moneda_original')
    def _compute_obtener_arancel_emision(self):
        for record in self:
            if record.instrumento_emision and ('bono' in record.instrumento_emision.lower() or re.search(r'\bbono\b', record.instrumento_emision, re.IGNORECASE)):
                if 90 <= record.plazo_por_titulo < 365:
                    record.emision_tasa_arancel = 0.0004
                elif 366 <= record.plazo_por_titulo < 730:
                    record.emision_tasa_arancel = 0.0005
                elif record.plazo_por_titulo >= 731:
                    record.emision_tasa_arancel = 0.0007

            elif record.instrumento_emision and 'acciones' in record.instrumento_emision.lower():
                if 0 <= record.monto_moneda_original <= 6500000000:
                    record.emision_tasa_arancel = 2500000
                elif record.monto_moneda_original >= 6500000001:
                    record.emision_tasa_arancel = 0.0004

            elif record.instrumento_emision and 'fondos' in record.instrumento_emision.lower():
                if 0 <= record.monto_moneda_original <= 6500000000:
                    record.emision_tasa_arancel = 2500000
                elif 6500000001 <= record.monto_moneda_original <= 100000000000000:
                    record.emision_tasa_arancel = 0.0004
            else:
                record.emision_tasa_arancel = 0.0002

    @api.depends('monto_moneda_original', 'dias_reporte', 'custodia_tasa_arancel', 'emision_tasa_arancel')
    def _compute_arancel_custodia_pyg(self):
        for record in self:
            if record.custodia_tasa_arancel == 0.0001:  # es decir... es BONO
                record.custodia_arancel = record.monto_moneda_original * (record.custodia_tasa_arancel / 365) * record.dias_reporte
                record.emision_arancel = record.monto_moneda_original * record.emision_tasa_arancel
            else:
                if record.emision_tasa_arancel == 2500000:
                    record.emision_arancel = 2500000
                else:
                    record.emision_arancel = record.monto_moneda_original * record.emision_tasa_arancel

    # @api.onchange('instrumento_emision', 'plazo_emision', 'monto_moneda_original')
    # def _onchange_instrumento_emision(self):
    #     self._compute_obtener_arancel_emision()
    #     self._compute_arancel_custodia_pyg()

    @api.depends('emision_arancel')
    def _compute_emision_iva(self):
        if self.emision_arancel:
            self.emision_iva = self.emision_arancel * 0.1

    @api.depends('emision_arancel','emision_iva')
    def _compute_emision_total(self):
        if self.emision_iva != 0:
            self.emision_total = self.emision_arancel + self.emision_iva


    @api.depends('custodia_arancel')
    def _compute_custodia_arancel_iva(self):
        if self.custodia_arancel:
            self.custodia_iva = self.custodia_arancel * 0.1

    @api.depends('custodia_arancel','custodia_iva')
    def _compute_custodia_total(self):
        if self.custodia_iva != 0:
            self.custodia_total = self.custodia_arancel + self.custodia_iva



    #onchange para el plazo_emision remanente (dias de reporte)
    @api.depends('fecha_reporte','inicio_colocacion')
    def _compute_dias_reporte(self):
        for i in self:
            if i.fecha_reporte and i.inicio_colocacion:
                dif = i.fecha_reporte - i.inicio_colocacion
                i.dias_reporte = dif.days


    @api.depends('custodia_total','emision_total')
    def _compute_total_emision_custodia(self):
        self.total_emision_custodia = self.custodia_total + self.emision_total


    # Al elegir la moneda original, seteamos el TC
    
    @api.depends('currency_id')
    def _compute_currency_id(self):
        for record in self:
            try:
                # Obtenemos el TC del mes
                tc = self.env['res.currency.rate'].search([('currency_id', '=', record.currency_id.id)], limit=1)
                record.tc_cierre_mes = tc.inverse_company_rate
            except Exception as e:
                print(e)


    @api.depends('custodia_total','tc_cierre_mes')
    def _compute_custodia_arancel_pyg(self):
        if self.custodia_total != 0:
            if self.currency_id.name != 'PYG':
                self.custodia_arancel_pyg = self.custodia_total * self.tc_cierre_mes
            else:
                self.custodia_arancel_pyg = self.custodia_total
    # # Convertimos la moneda original a PYG
    
    
    
    @api.depends('monto_custodiado', 'currency_id')
    def _compute_monto_original(self):
        for record in self:
            # Si la divisa original es PYG, no hacemos nada
            if record.currency_id.name == 'PYG':
                record.monto_pyg = record.monto_original
            else:
                record.monto_pyg = record.monto_original * record.tc_cierre_mes


    def marcar_como_inactivo(self):
        self.state = 'inactivo'
        dialog = self.env['pbp.dialog.box'].sudo().search([])[-1]
        return {
            'type':'ir.actions.act_window',
            'name':'Message',
            'res_model':'pbp.dialog.box',
            'view_mode':'form',
            'target':'new',
            'res_id': dialog.id
        }

    #QUE TRAIGA DIRECTO DEL SISTEMA COLUMNA MONTOEMISIONTOTAL 
    @api.depends('cantidad_emitida', 'currency_id')
    def _compute_monto_custodiado(self):
        for record in self:
            if record.cantidad_emitida:
                if record.currency_id.name == 'USD':
                    record.monto_custodiado = record.cantidad_emitida * 1000
                    record.monto_moneda_original = record.monto_custodiado
                elif record.currency_id.name == 'PYG':
                    record.monto_custodiado = record.cantidad_emitida * 1000000
                    record.monto_moneda_original = record.monto_custodiado



    @api.depends('monto_custodiado')
    def _compute_arancel_anual(self):
        for record in self:
            if record.monto_custodiado:
                record.arancel_anual = record.monto_custodiado * 0.0001 #la tasa debe sacar de configuracion

    @api.depends('arancel_anual')
    def _compute_custodia_diaria(self):
        for record in self:
            if record.plazo_emision != 0:
                if record.arancel_anual:
                    record.custodia_diaria = record.arancel_anual / 365

                    # Si la moneda es PYG, redondear
                    if record.currency_id.name == 'PYG':
                        record.custodia_diaria = round(record.custodia_diaria, 0)
        
            else:
                record.custodia_diaria = 0

    @api.depends('plazo_emision', 'custodia_diaria')
    def _compute_arancel_custodia(self):
        for record in self:
            if record.plazo_emision > 0:
                record.arancel_custodia = record.custodia_diaria * record.plazo_emision
            else:
                record.arancel_custodia = record.arancel_anual

    @api.depends('arancel_custodia')
    def _compute_iva_custodia(self):
        for record in self:
            record.iva_custodia = record.arancel_custodia * 0.1

    @api.depends('arancel_custodia', 'iva_custodia')
    def _compute_total_custodia(self):
        for record in self:
            record.total_custodia = record.arancel_custodia + record.iva_custodia

            # Si la moneda es PYG, redondear
            if record.currency_id.name == 'PYG':
                record.arancel_custodia = round(record.arancel_custodia, 0)
                record.iva_custodia = round(record.iva_custodia, 0)
                record.total_custodia = round(record.total_custodia, 0)


    def generar_facturas(self, records=None):
        if records:
            novedades = records.read((set(self.env['pbp.novedades_sen']._fields)))
            novedades = [novedad for novedad in novedades if novedad['state'] == 'pendiente']
        else:
            novedades = self.env['pbp.novedades_sen'].search_read([
                ['state', '=', 'pendiente'],
                #['fecha_emision', '>=', from_date],
                #['fecha_emision', '<=', to_date],
            ])

        data = generar_facturas(self.env, novedades)

        error_msg = ''
        if data.get('novedades_sen_sin_partners_ids') or data.get('novedades_sen_sin_productos_ids'):
            error_msg = 'No se pudieron generar algunas facturas debido a datos faltantes en Novedades.'

        dialog = self.env['pbp.dialog.box'].sudo().create({
            'error_msg': error_msg,
            'novedades_sen_sin_partners_ids': data['novedades_sen_sin_partners_ids'],
            'novedades_sen_sin_productos_ids':  data['novedades_sen_sin_productos_ids'],
            'novedades_sen_sin_cuentas_ids':  data['novedades_sen_sin_cuentas_ids'],
            'invoice_ids': data['facturas_ids'],
            'novedades_sen_publicadas_ids': data['novedades_sen_publicadas_ids'],
        })
        return{
            'type':'ir.actions.act_window',
            'name':'Message',
            'res_model':'pbp.dialog.box',
            'view_mode':'form',
            'target':'new',
            'res_id': dialog.id
        }

    @api.model
    def sincronizar_registros(self, data):
        """
        Método que se encarga de recibir los datos del control de pago a través de XMLRPC
        """
        # Instanciamos el objeto de logs
        sync_log_obj = self.env['pbp.sincronizacion_logs'].sudo().create(
            {"tipo_sincronizacion": 'Novedades Sen'})
        self._cr.commit()

        try:
            cantidad = len(data)
            _logger.info(f"Sincronizando: {cantidad}")

            # Guardamos un log del registro sicronizado
            sync_log_obj.write(
                {
                    'cant_registros_obtenidos': cantidad,
                }
            )
            self._cr.commit()

            # Iteramos por cada registro para guardar en la BD
            for d in data:
                self.guardar_sen(d, sync_log_obj)

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar proformas")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_sen(self, sen, sync_log_obj):
        """
        Formatear los datos de la liquidacion y guardarlos en la tabla
        """
        try:
            partner_id = False
            partners = self.env['res.partner'].search([('id_cliente_pbp', '=', sen['persona_id'])])
            partner = partners[0] if partners else False
            if partner:
                partner_ruc = partner['vat']
                partner_ids = self.env['res.partner'].search([('vat', '=', partner_ruc)])
                if len(partner_ids) > 1:
                    max_total = 0
                    for pid in partner_ids:
                        partner_novedades_total = len(self.env['pbp.novedades'].search([('partner_id', '=', pid.id)]))
                        if partner_novedades_total > max_total:
                            partner_id = pid.id
                            max_total = partner_novedades_total
                    if not max_total:
                        partner_id = partner['id']
                else:
                    partner_id = partner['id']

            sen['partner_id'] = partner_id

            if not partner_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': sen,
                        'error_msg': "No se encuentra el emisor %s" % sen['emisor_id'],
                    }
                )
            else:
                self.env['pbp.novedades_sen'].sudo().create(sen)
        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': sen,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()


    @api.model
    def create(self, vals):
        _logger.info("ENTRO ACA AL MENOS")
        # Llamar al método create original para crear el registro
        record = super(NovedadesSEN, self).create(vals)
        
        if not record.partner_id or not record.product_id:
            _logger.error("El registro debe tener un cliente y un producto asociados para crear la factura.")
            raise UserError("El registro debe tener un cliente y un producto asociados para crear la factura.")
        
        # Crear la factura
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': record.partner_id.id,
            'currency_id': record.currency_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': record.product_id.id,
                    'quantity': 1,
                    'price_unit': record.monto_custodiado,
                    'tax_ids': [(6, 0, [1])],  # Asignar el impuesto con ID=1
                }),
                (0, 0, {
                    'product_id': 157 if record.instrumento in ['Bono Financiero', 'Bono', 'bono'] else 158,
                    'quantity': 1,  
                    'price_unit': record.custodia_total if record.instrumento in ['Bono Financiero', 'Bono', 'bono'] else record.emision_total, 
                    'tax_ids': [(6, 0, [1])],  # Asignar el impuesto con ID=1 (10%)
                })
            ]
        }
                
        # Crear la factura usando el modelo account.move
        try:
            invoice = self.env['account.move'].create(invoice_vals)
        except Exception as e:
            _logger.error(f"Error al crear la factura: {str(e)}")
            raise UserError("Error al crear la factura.")
        
        if not invoice:
            _logger.error("No se pudo crear la factura.")
            raise UserError("Error al crear la factura.")
        
        record.invoice_id = invoice.id
        _logger.info(f"Factura creada exitosamente para el registro {record.id}")
        
        return record
    

############################################
    @api.depends('tipo_instrumento_id')
    def _onchange_tipo_instrumento_id(self):
        if self.tipo_instrumento_id:
            config = self.env['pbp.configuracion_instrumento'].search([('tipo_instrumento_id', '=', self.tipo_instrumento_id.id)], limit=1)
            if config:
                self.product_emision_id = config.producto_por_defecto_id

    
    ############################################ Configuracion Instrumento 
class ConfiguracionInstrumento(models.Model):
    _name = 'pbp.configuracion_instrumento'
    _description = 'Configuración de Instrumentos'

    name = fields.Char(string='Nombre', required=True)
    tipo_instrumento_id = fields.Many2one('pbp.tipo_instrumento', string='Tipo de Instrumento', required=True)
    producto_por_defecto_id = fields.Many2one('product.product', string='Producto por Defecto')


class TipoInstrumento(models.Model):
    _name = 'pbp.tipo_instrumento'
    _description = 'Tipo de Instrumento'

    name = fields.Char(string='Nombre', required=True)
