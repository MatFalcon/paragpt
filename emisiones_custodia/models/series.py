# -*- coding: utf-8 -*-

from odoo import api, exceptions, fields, models
import logging

_logger = logging.getLogger(__name__)


class EmisionesCustodia(models.Model):
    _name = 'emisiones.series'
    _description = 'Tabla para reporte series'

    name = fields.Char(string="Serie")
    partner_id = fields.Many2one('res.partner', string="Emisor", required=True)
    cod_emisor = fields.Char(string="Cod. Emisor")
    monto_original = fields.Monetary(string="Monto en moneda Original")
    monto_pyg = fields.Monetary(string="Monto en PYG")
    inicio_colocacion = fields.Date(string="Inicio Colocación")
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento")
    #fecha_reporte = fields.Date(string="Fecha de Reporte")
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True)
    plazo = fields.Integer(string="Plazo")
    #dias_reporte = fields.Integer(string="Días de reporte")
    instrumento = fields.Char(string="Instrumento")
    tasa_instrumento = fields.Float(string="Tasa del Instrmento")

    @api.model
    def sincronizar_registros(self, data):
        """
        Método que se encarga de recibir los datos del control de pago a través de XMLRPC
        """
        # Instanciamos el objeto de logs
        sync_log_obj = self.env['pbp.sincronizacion_logs'].sudo().create(
            {"tipo_sincronizacion": 'Emisiones Series'})
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
                self.guardar_emisiones_series(d, sync_log_obj)

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar emisiones series")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_emisiones_series(self, emisiones_series, sync_log_obj):
        """
        Formatear los datos de la compensacion de rueda anterior y guardarlos en la tabla
        """
        try:
            name = emisiones_series['name']
            cod_emisor = emisiones_series['cod_emisor']
            emisor_id = emisiones_series['emisor_id']
            monto_original = emisiones_series['monto_original']
            inicio_colocacion = emisiones_series['inicio_colocacion']
            fecha_vencimiento = emisiones_series['fecha_vencimiento']
            instrumento = emisiones_series['instrumento']
            tasa_instrumento = emisiones_series['tasa_instrumento']
            plazo = emisiones_series['plazo']
            moneda_id = emisiones_series['moneda_id']

            if moneda_id == 2:
                # currency_name = 'USD'
                currency_id = 2
            elif moneda_id == 1:
                # currency_name = 'PYG'
                currency_id = 155
            else:
                return False

            partner_id = False
            partners = self.env['res.partner'].search([('id_cliente_pbp', '=', emisor_id)])
            partner = partners[0] if partners else False
            if partner:
                partner_ruc = partner['vat']
                partner_ids = self.env['res.partner'].search([('vat', '=', partner_ruc)])
                if len(partner_ids) > 1:
                    max_total = 0
                    for pid in partner_ids:
                        partner_novedades_total = len(
                            self.env['pbp.novedades'].search([('partner_id', '=', pid.id)]))
                        if partner_novedades_total > max_total:
                            partner_id = pid.id
                            max_total = partner_novedades_total
                    if not max_total:
                        partner_id = partner['id']
                else:
                    partner_id = partner['id']

            emisiones = self.env['emisiones.series'].search(
                [('name', '=', name)])

            obj = {
                'name': name,
                'cod_emisor': cod_emisor,
                'monto_original': monto_original,
                'inicio_colocacion': inicio_colocacion,
                'fecha_vencimiento': fecha_vencimiento,
                'currency_id': currency_id,
                'instrumento': instrumento,
                'tasa_instrumento': tasa_instrumento,
                'partner_id': partner_id,
                'plazo':plazo
            }

            if not partner_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': emisiones_series,
                        'error_msg': "No se encuentra el emisor %s" % emisor_id,
                    }
                )
            else:
                if emisiones:
                    emisiones.sudo().write(obj)
                else:
                    self.env['emisiones.series'].sudo().create(obj)
        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': emisiones_series,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()
