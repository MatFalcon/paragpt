from odoo import api, models, fields
import logging
import datetime

_logger = logging.getLogger(__name__)


class Novedades(models.Model):
    _name = 'pbp.novedades'
    _order = 'state, fecha_operacion desc'
    _rec_name = 'id_pbp'

    _sql_contraints = ['uniq_id_pbp', 'unique(id_pbp)', 'Ya existe un registro con el mismo id_pbp']

    id_pbp = fields.Integer(required=False, string='ID Comision')
    id_vvalores = fields.Integer(string='ID vValores')
    fecha_operacion = fields.Date(required=True, string='Fecha de operación')
    fecha_vencimiento = fields.Date(required=False, string='Fecha de vencimiento')
    plazo = fields.Integer(required=False, string="Plazo")
    cliente_id = fields.Integer(required=True, string="ID Cliente PBP")
    # precio_unitario = fields.Float(required=True)
    cantidad = fields.Integer(required=True, string="Cantidad")
    subtotal2 = fields.Float(string='Total', compute="_compute_subtotal", store=False, digits=(17, 3))
    subtotal = fields.Float(string='Total', digits=(17, 3))
    tasa_interes = fields.Float(string='Tasa de interés', digits=(17, 3))
    contrato_descripcion = fields.Char(required=True)
    contrato_id = fields.Integer(required=True)
    contrato_tipo_descripcion = fields.Char(required=True)
    mercado = fields.Char(string="Mercado")
    comision_detalle = fields.Char()
    instrumento = fields.Char(string="Instrumento")
    volumen_gs = fields.Monetary(string='Volumen Negociado')
    volumen_gs_usd = fields.Monetary(string='Volumen Negociado (USD)')
    liquidacion = fields.Float(string='Liquidación', digits=(17, 6))
    porcentaje = fields.Float()
    # total_gravada = fields.Float(compute='_compute_total_gravada', store=True, string='Total Gravada')
    total_iva = fields.Float(string='Total IVA')
    total = fields.Float(string='Total Gravada')

    tipo_operacion = fields.Selection(
        selection=[
            ('Compra', 'Compra'),
            ('Venta', 'Venta'),
            ('Reportado', 'Reportado'),
            ('Reportador', 'Reportador'),
        ],
        string='Tipo de Operación',
    )

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
    invoice_id = fields.Many2one('account.move', string="Factura")

    @api.model
    def create(self, *args, **kwargs):
        record = super().create(*args, **kwargs)
        self.env['pbp.novedades_pbp'].create([{'novedades_default_id': record.id}])
        return record

    def marcar_como_inactivo(self):
        self.state = 'inactivo'
        dialog = self.env['pbp.dialog.box'].sudo().search([])[-1]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Message',
            'res_model': 'pbp.dialog.box',
            'view_mode': 'form',
            'target': 'new',
            'res_id': dialog.id
        }

    def _compute_subtotal(self):
        for novedad in self:
            novedad.subtotal2 = novedad.total + novedad.total * 0.1
            novedad.subtotal = round(novedad.subtotal2, 3)

    @api.model
    def sincronizar_registros(self, data):
        """
        Método que se encarga de recibir los datos del control de pago a través de XMLRPC
        """
        # Instanciamos el objeto de logs
        sync_log_obj = self.env['pbp.sincronizacion_logs'].sudo().create(
            {"tipo_sincronizacion": 'Novedades'})
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
            c = 1
            for d in data:
                print(c)
                self.guardar_novedades(d, sync_log_obj)
                c = c + 1

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar Novedades")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_novedades(self, novedades, sync_log_obj):
        """
        Formatear los datos de la liquidacion y guardarlos en la tabla
        """
        try:
            partner_id = False
            partners = self.env['res.partner'].search([('id_cliente_pbp', '=', novedades['cliente_id'])])
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

                novedades['partner_id'] = partner_id

                mercado = novedades['mercado']
                instrumento = novedades['instrumento']
                volumen_gs = novedades['volumen_gs']
                plazo = novedades['plazo']
                product_id = False

                partner_name = partner.name

                if partner_name.lower() in 'ministerio de hacienda' and mercado == 'Mercado Primario':
                    product_id = 240
                    total = (volumen_gs / 100) * 0.01
                elif (mercado == 'Mercado Primario' or mercado == 'Mercado Secundario') and (
                        instrumento == 'Fondos de Inversión' or instrumento == 'Acciones'):
                    total = (volumen_gs / 100) * 0.02
                    product_id = 154
                elif (mercado == 'Mercado Primario' or mercado == 'Mercado Secundario') and (
                        'bono' in instrumento.lower() or 'bbcp' in instrumento.lower()):
                    product_id = 153
                    if partner_name.lower() in 'ministerio de hacienda' and mercado == 'Mercado Primario':
                        product_id = 240
                        total = (volumen_gs / 100) * 0.01
                    else:
                        total = (volumen_gs / 100) * 0.02
                elif mercado == 'Repos':
                    product_id = 155
                    if 1 <= plazo <= 6:
                        arancel_repo = 0.0015
                    elif 7 <= plazo <= 14:
                        arancel_repo = 0.001
                    elif 15 <= plazo <= 29:
                        arancel_repo = 0.0008
                    elif 30 <= plazo <= 89:
                        arancel_repo = 0.0006
                    else:
                        arancel_repo = 0.0005

                    arancel_anual = volumen_gs * arancel_repo
                    total = arancel_anual / 365 * plazo

                    if novedades['currency_id'] == 155 and total < 10000:
                        total = 10000
                    elif novedades['currency_id'] == 2:
                        rate = self.env['res.currency.rate'].search([('name', '=', novedades['fecha_operacion'])])
                        if rate:
                            rate_compra = rate.inverse_company_rate_tipo_cambio_comprador
                            if (total * rate_compra) < 10000:
                                total = 10000 / rate_compra

                total_iva = round(total * 0.1, 2)
                if novedades['currency_id'] == 155:
                    subtotal = round(total + total_iva)
                else:
                    subtotal = round(total + total_iva, 2)

                novedades['product_id'] = product_id
                novedades['total'] = total
                novedades['total_iva'] = round(total_iva, 2)
                novedades['subtotal'] = subtotal

                novedad_anterior = self.env['pbp.novedades'].search([('id_vvalores', '=', novedades['id_vvalores'])])

                if novedad_anterior:
                    self.env['pbp.novedades'].sudo().write(novedades)
                    print('escrito')
                else:
                    self.env['pbp.novedades'].sudo().create(novedades)
                    print('creado')

            else:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': novedades,
                        'error_msg': "No se encuentra el emisor %s" % novedades['cliente_id'],
                    }
                )

        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': novedades,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()
