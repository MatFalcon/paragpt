from odoo import models, fields, api

from odoo.addons.pbp.facturas.generador import generar_facturas
import logging

_logger = logging.getLogger(__name__)


class OperacionFuturo(models.Model):
    _name = 'pbp.operacion_futuro'
    _order = 'fecha desc'

    operacion_cartera_id = fields.Integer(required=True, string="Operacion Cartera ID")
    fecha = fields.Date(string='Fecha')
    mercado = fields.Char(string="Mercado")
    producto_descripcion = fields.Char(string="Producto")
    currency_id = fields.Many2one('res.currency', required=False, string="Moneda")
    precio = fields.Float(required=False, string="Precio")
    cantidad = fields.Float(required=False, string="Cantidad")
    importe = fields.Float(required=False, string="Importe")
    miembro_compensador_id = fields.Many2one('res.partner', string="Miembro Compensador")
    cuenta_registro_cod = fields.Char(string="Cuenta Registro Código")
    contrato = fields.Char(string="Contrato descripción")
    volumen = fields.Float(string="Volumen")
    tipo_operacion = fields.Selection(
        selection=[
            ('Compra', 'Compra'),
            ('Venta', 'Venta')
        ],
        required=True,
        string='Tipo de Operación',
    )
    hora_ingreso = fields.Char(string="Hora de Ingreso")
    proceso_descripcion = fields.Char(string="Proceso Descripción")
    fecha_liquidacion_contrato = fields.Date(string="Fecha Liquidación Contrato")


    @api.model
    def sincronizar_registros(self, data):
        """
        Método que se encarga de recibir los datos del control de pago a través de XMLRPC
        """
        # Instanciamos el objeto de logs
        sync_log_obj = self.env['pbp.sincronizacion_logs'].sudo().create(
            {"tipo_sincronizacion": 'Futuro'})
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
                self.guardar_futuro(d, sync_log_obj)

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar operaciones a futuro")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_futuro(self, futuro, sync_log_obj):
        """
        Formatear los datos de la liquidacion y guardarlos en la tabla
        """
        try:
            if futuro['producto_descripcion'] == 'Dólar Americano':
                futuro['currency_id'] = 2
            futuros = self.env['pbp.operacion_futuro'].search([('operacion_cartera_id','=',futuro['operacion_cartera_id'])])
            miembro_compensador_id_sis = futuro['miembro_compensador_id']
            miembros_compensadores = self.env['res.partner'].search(
                [('id_cliente_pbp', '=', miembro_compensador_id_sis)])
            miembro_compensador_id = False
            miembro_compensador = miembros_compensadores[0] if miembros_compensadores else False
            if miembro_compensador:
                partner_ruc = miembro_compensador['vat']
                partner_ids = self.env['res.partner'].search([('vat', '=', partner_ruc)])
                if len(partner_ids) > 1:
                    max_total = 0
                    for pid in partner_ids:
                        miembro_compensador_novedades_total = len(
                            self.env['pbp.novedades'].search([('partner_id', '=', pid.id)]))
                        if miembro_compensador_novedades_total > max_total:
                            miembro_compensador_id = pid.id
                            max_total = miembro_compensador_novedades_total
                    if not max_total:
                        miembro_compensador_id = miembro_compensador['id']
                else:
                    miembro_compensador_id = miembro_compensador['id']
            if not miembro_compensador_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': futuro,
                        'error_msg': "No se encuentra el miembro compensador %s" % miembro_compensador_id_sis,
                    }
                )
            else:
                futuro['miembro_compensador_id'] = miembro_compensador_id
                if futuros:
                    futuros.sudo().write(futuro)
                else:
                    self.env['pbp.operacion_futuro'].sudo().create(futuro)
        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': futuro,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()
