from odoo import models, fields, api

from odoo.addons.pbp.facturas.generador import generar_facturas
import logging

_logger = logging.getLogger(__name__)


class NovedadesSEN(models.Model):
    _name = 'pbp.novedades_sen'
    _order = 'state, fecha_emision desc'

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

    state = fields.Selection(
        selection=[
            ('inactivo', 'Inactivo'),
            ('pendiente', 'Pendiente'),
            ('draft', 'Draft'),
            ('publicado', 'Publicado'),
        ],
        required=True,
        default='pendiente',
        string='Estado',
    )

    partner_id = fields.Many2one('res.partner', string="Cliente")
    currency_id = fields.Many2one('res.currency', required=True, string="Moneda")
    product_id = fields.Many2one('product.product', string='Producto')
    invoice_id = fields.Many2one('account.move', string='Factura')

    # Campos para calcular
    monto_custodiado = fields.Float()
    fecha_inicial = fields.Date()
    plazo = fields.Integer()
    arancel_anual = fields.Float()
    custodia_diaria = fields.Float()
    arancel_custodia = fields.Float()
    iva_custodia = fields.Float()
    total_custodia = fields.Float()

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

    @api.onchange('cantidad_emitida', 'currency_id')
    def _cantidad_emitida_onchange(self):
        if self.cantidad_emitida:
            if self.currency_id.name == 'USD':
                self.monto_custodiado = self.cantidad_emitida * 1000
            elif self.currency_id.name == 'PYG':
                self.monto_custodiado = self.cantidad_emitida * 1000000

    @api.onchange('fecha_inicial', 'fecha_vencimiento')
    def _fecha_inicial_onchange(self):
        if self.fecha_inicial and self.fecha_vencimiento:
            plazo = (self.fecha_vencimiento - self.fecha_inicial).days + 1
            self.plazo = plazo if plazo > 0 else 0
        else:
            self.plazo = 0

    @api.onchange('monto_custodiado')
    def _monto_custodiado_onchange(self):
        if self.monto_custodiado:
            self.arancel_anual = self.monto_custodiado * 0.0001

    @api.onchange('arancel_anual')
    def _arancel_anual_onchange(self):
        if self.arancel_anual:
            self.custodia_diaria = self.arancel_anual / 365

            # Si la moneda es PYG, redondear
            if self.currency_id.name == 'PYG':
                self.custodia_diaria = round(self.custodia_diaria, 0)

    @api.onchange('plazo', 'monto_custodiado', 'arancel_anual')
    def _plazo_onchange(self):
        if self.plazo > 0:
            self.arancel_custodia = self.custodia_diaria * self.plazo
        else:
            self.arancel_custodia = self.arancel_anual

        self.iva_custodia = self.arancel_custodia * 0.1
        self.total_custodia = self.arancel_custodia + self.iva_custodia

        # Si la moneda es PYG, redondear
        if self.currency_id.name == 'PYG':
            self.arancel_custodia = round(self.arancel_custodia, 0)
            self.iva_custodia = round(self.iva_custodia, 0)
            self.total_custodia = round(self.total_custodia, 0)

    def calcular_valores(self):
        novedades = self.env['pbp.novedades_sen'].search([['state', '=', 'pendiente']])
        for novedad in novedades:
            novedad._cantidad_emitida_onchange()
            novedad._fecha_inicial_onchange()
            novedad._monto_custodiado_onchange()
            novedad._arancel_anual_onchange()
            novedad._plazo_onchange()
        return True

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
            partners = self.env['res.partner'].search([('id_cliente_pbp', '=', sen['emisor_id'])])
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
