# -*- coding: utf-8 -*-

import datetime
from odoo import models, fields, api
import re
import logging
from odoo.exceptions import UserError
from datetime import date

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
    ruc = fields.Char(string="RUC")
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
    custodia_arancel_pyg = fields.Monetary(string="Arancel Custodia en PYG", compute="_compute_custodia_arancel_pyg", store=True)
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

    @api.depends('fecha_vencimiento', 'inicio_colocacion')
    def _compute_plazo_por_titulo(self):
        for record in self:
            if record.fecha_vencimiento and record.inicio_colocacion:
                # Calcular el plazo solo si ambos campos son fechas válidas
                if isinstance(record.fecha_vencimiento, date) and isinstance(record.inicio_colocacion, date):
                    record.plazo_por_titulo = (record.fecha_vencimiento - record.inicio_colocacion).days
                else:
                    record.plazo_por_titulo = 0
            else:
                record.plazo_por_titulo = 0

    #onchange para el producto de emision y custodia
    @api.depends('instrumento')
    def _compute_instrumento(self):
        for record in self:
            if record.instrumento in ['Bono Financiero', 'Bono', 'bono']:
                record.product_custodia_id = 165
                record.product_emision_id = 157
                record.instrumento_emision = record.instrumento
            else:
                record.product_custodia_id = False
                record.product_emision_id = 158
                record.instrumento_emision = record.instrumento

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
        for record in self:
            if record.instrumento_emision and (
                    record.instrumento_emision.lower() == "bono" or re.search(r'\bbono\b', record.instrumento_emision,
                                                                              re.IGNORECASE)):
                record.custodia_tasa_arancel = 0.0001
            else:
                record.custodia_tasa_arancel = 0

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
        for record in self:
            if record.emision_arancel:
                record.emision_iva = record.emision_arancel * 0.1
            else:
                record.emision_iva = 0  # Asegurarse de que el campo esté siempre inicializado

    @api.depends('emision_arancel', 'emision_iva')
    def _compute_emision_total(self):
        for record in self:
            if record.emision_iva != 0:
                record.emision_total = record.emision_arancel + record.emision_iva
            else:
                record.emision_total = record.emision_arancel  # Asignar emision_arancel si emision_iva es 0

    @api.depends('custodia_arancel')
    def _compute_custodia_arancel_iva(self):
        for record in self:
            if record.custodia_arancel:
                record.custodia_iva = record.custodia_arancel * 0.1
            else:
                record.custodia_iva = 0  # Asegurarse de que el campo esté siempre inicializado

    @api.depends('custodia_arancel', 'custodia_iva')
    def _compute_custodia_total(self):
        for record in self:
            if record.custodia_iva != 0:
                record.custodia_total = record.custodia_arancel + record.custodia_iva
            else:
                record.custodia_total = record.custodia_arancel  # Asignar custodia_arancel si custodia_iva es 0


    #onchange para el plazo_emision remanente (dias de reporte)
    @api.depends('fecha_reporte','inicio_colocacion')
    def _compute_dias_reporte(self):
        for i in self:
            if i.fecha_reporte and i.inicio_colocacion:
                dif = i.fecha_reporte - i.inicio_colocacion
                i.dias_reporte = dif.days


    @api.depends('custodia_total','emision_total')
    def _compute_total_emision_custodia(self):
        for rec in self:
            rec.total_emision_custodia = rec.custodia_total + rec.emision_total


    # Al elegir la moneda original, seteamos el TC
    
    @api.depends('currency_id')
    def _compute_currency_id(self):
        for record in self:
            try:
                # Obtenemos el TC del mes
                tc = self.env['res.currency.rate'].search([('currency_id', '=', record.currency_id.id)], limit=1)
                record.tc_cierre_mes = tc.set_venta
            except Exception as e:
                print(e)

    @api.depends('custodia_total', 'tc_cierre_mes')
    def _compute_custodia_arancel_pyg(self):
        for record in self:
            if record.custodia_total != 0:
                if record.currency_id.name != 'PYG':
                    record.custodia_arancel_pyg = record.custodia_total * record.tc_cierre_mes
                else:
                    record.custodia_arancel_pyg = record.custodia_total
            else:
                record.custodia_arancel_pyg = 0  # Inicializar en 0 si custodia_total es 0

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
                domain = [
                    ('persona_id', '=', d.get('persona_id')), #check
                    ('emisor_id', '=', d.get('emisor_id')), #check
                    ('cod_negociacion', '=', d.get('cod_negociacion')), #check
                    ('contrato_id', '=', d.get('contrato_id')), #check
                    ('cantidad_emitida', '=', d.get('cantidad_emitida')), #check
                    ('product_id', '=', d.get('product_id')), #check
                ]
                sen_ya_existe = self.env['pbp.novedades_sen'].search(domain)
                if sen_ya_existe:
                    continue

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
            existing_sens = self.env['pbp.novedades_sen'].search([('cod_negociacion', '=', sen['cod_negociacion'])])
            if existing_sens:
                _logger.info(f"Record with cod_negociacion {sen['cod_negociacion']} already exists.")
                return
            partner_id = partners[0]['id'] if partners else False
            sen['partner_id'] = partner_id
            if not partner_id:
                ####En caso de no existir un contacto con id_cliente_pbp buscamos por ruc
                ruc = sen['ruc'].split('-')[0] ##obtenemos el RUC sin DV
                partners = self.env['res.partner'].search([('ruc', '=', ruc)])
                partner_id = partners[0]['id'] if partners else False
                sen['partner_id'] = partner_id
                if not partner_id:
                    #### EN CASO DE NO EXISTIR CLIENTE NI POR RUC NI POR ID PBP SE CREA UNO NUEVO
                    sen['partner_id']=self.create_cliente(sen['ruc'],sen['persona_id'],sen['emisor_descripcion'])
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

    def create_cliente(self,ruc,id_cliente_pbp,emisor_descripcion):
        if ruc and id_cliente_pbp and emisor_descripcion:
            ruc = ruc.split('-')[0] #OBTENEMOS EL VALOR DEL RUC SIN DV
            tipo_identificacion = self.env.ref('paraguay_backoffice.tipo_identificacion_1').id
            res_partner_obj = self.env['res.partner']
            res_partner_vals = {
                'name':emisor_descripcion,
                'id_cliente_pbp':id_cliente_pbp,
                'ruc': ruc,
                'tipo_identificacion': tipo_identificacion
            }
            res_partner_obj.create(res_partner_vals)
            return res_partner_obj.id #RETORNAMOS EL ID DEL NUEVO CLIENTE
        else:
            _logger.error(f"El registro {self.id} no tiene los datos suficientes para clear el cliente")

    @api.model
    def generar_facturas(self, records):
        # Validaciones
        partners = records.mapped('partner_id')
        if len(partners) > 1:
            raise UserError("No se puede generar una factura con mas de un cliente")
        partner = partners[0]

        # Agrupar montos por producto
        product_totals = {}
        for rec in records.filtered(lambda r: r.state != 'done'):
            # emision
            pid = rec.product_emision_id.id
            product_totals[pid] = product_totals.get(pid, 0.0) + rec.emision_total
            # custodia / emision alterna
            pid2 = rec.product_custodia_id.id
            amt2 = (rec.custodia_total
                    if rec.instrumento.lower().startswith('bono')
                    else rec.emision_total)
            product_totals[pid2] = product_totals.get(pid2, 0.0) + amt2

        # Construir lineas de factura
        lines = [
            (0, 0, {
                'product_id': prod_id,
                'quantity': 1,
                'price_unit': total,
                'tax_ids': [(6, 0, [1])],
                'analytic_distribution': {1: 100.0},
            })
            for prod_id, total in product_totals.items()
        ]

        # Crear la factura directamente
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'currency_id': records[0].currency_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': lines,
        }
        invoice = self.env['account.move'].create(invoice_vals)

        # Marcar los registros como hecho
        records.write({'state': 'done'})

        # Abrir la factura en pantalla
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': invoice.id,
            'target': 'current',
        }
    def calcular_valores(self):
        novedades = self.env['pbp.novedades_sen'].search([['state', '=', 'pendiente']])
        for novedad in novedades:
            novedad._cantidad_emitida_onchange()
            novedad._fecha_inicial_onchange()
            novedad._monto_custodiado_onchange()
            novedad._arancel_anual_onchange()
            novedad._plazo_onchange()
        return True
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
