from odoo import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)


class TransferenciaCartera(models.Model):
    _name = "pbp.transferencia_cartera"
    _description = "Modelo de Transferencia de Carteras"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'id'

    id_pbp = fields.Integer(string="ID PBP", required=True)
    emisor_id = fields.Many2one('res.partner', string="Emisor", required=True, tracking=True)
    receptor_id = fields.Many2one('res.partner', string="Receptor", required=True, tracking=True)
    fecha = fields.Date(string="Fecha", required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(
        'res.currency', string="Moneda", default=lambda self: self.env.user.company_id.currency_id)
    monto = fields.Monetary(string="Monto", required=False, tracking=True)
    motivo = fields.Text(string="Motivo", required=True, tracking=True)
    invoice_id = fields.Many2one('account.move', string='Factura')

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            jornal = self.env['mantenimiento_registro.jornal_mantenimiento'].search([('activo', '=', True)])
            if jornal:
                val['monto'] = jornal.monto
        recs = super(TransferenciaCartera, self).create(vals_list)
        return recs

    @api.model
    def sincronizar_registros(self, data):
        """
        Método que se encarga de recibir los datos del control de pago a través de XMLRPC
        """
        # Instanciamos el objeto de logs
        sync_log_obj = self.env['pbp.sincronizacion_logs'].sudo().create(
            {"tipo_sincronizacion": 'Transferencia de Cartera'})
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
                self.guardar_transferencia_cartera(d, sync_log_obj)

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar transferencia de cartera")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_transferencia_cartera(self, transferencia_cartera, sync_log_obj):
        """
        Formatear los datos de la transferencia cartera y guardarlos en la tabla
        """
        try:

            emisor_id_sis = transferencia_cartera['emisor_id']
            receptor_id_sis = transferencia_cartera['receptor_id']
            emisor_id = False
            receptor_id = False

            emisores = self.env['res.partner'].search([('id_cliente_pbp', '=', emisor_id_sis)])
            emisor = emisores[0] if emisores else False
            if emisor:
                partner_ruc = emisor['vat']
                partner_ids = self.env['res.partner'].search([('vat', '=', partner_ruc)])
                if len(partner_ids) > 1:
                    max_total = 0
                    for pid in partner_ids:
                        emisor_novedades_total = len(self.env['pbp.novedades'].search([('partner_id', '=', pid.id)]))
                        if emisor_novedades_total > max_total:
                            emisor_id = pid.id
                            max_total = emisor_novedades_total
                    if not max_total:
                        emisor_id = emisor['id']
                else:
                    emisor_id = emisor['id']

            receptores = self.env['res.partner'].search([('id_cliente_pbp', '=', receptor_id_sis)])
            receptor = receptores[0] if receptores else False
            if receptor:
                partner_ruc = receptor['vat']
                partner_ids = self.env['res.partner'].search([('vat', '=', partner_ruc)])
                if len(partner_ids) > 1:
                    max_total = 0
                    for pid in partner_ids:
                        receptor_compensador_novedades_total = len(self.env['pbp.novedades'].search([('partner_id', '=', pid.id)]))
                        if receptor_compensador_novedades_total > max_total:
                            receptor_id = pid.id
                            max_total = receptor_compensador_novedades_total
                    if not max_total:
                        receptor_id = receptor['id']
                else:
                    receptor_id = receptor['id']

            transferencia_carteras = self.env['pbp.transferencia_cartera'].search([('id_pbp', '=', transferencia_cartera['id_pbp'])])

            transferencia_cartera['receptor_id'] = receptor_id
            transferencia_cartera['emisor_id'] = emisor_id

            if not emisor_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': transferencia_cartera,
                        'error_msg': "No se encuentra el emisor %s" % emisor_id_sis,
                    }
                )
            if not receptor_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': transferencia_cartera,
                        'error_msg': "No se encuentra el receptor %s" % receptor_id_sis,
                    }
                )
            if receptor_id and emisor_id:
                if transferencia_carteras:
                    transferencia_carteras.sudo().write(transferencia_cartera)
                else:
                    self.env['pbp.transferencia_cartera'].sudo().create(transferencia_cartera)
        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': transferencia_cartera,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()
