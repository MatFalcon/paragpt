from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)


class Liquidaciones(models.Model):
    _name = "pbp.liquidaciones"
    _description = "Modelo de Liquidaciones"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'id'

    id_pbp = fields.Integer(string="ID PBP", required=True)
    cliente_id = fields.Integer(required=True, string="ID Cliente PBP",tracking=True)
    partner_id = fields.Many2one('res.partner', string="Cliente", required=True, tracking=True)
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento", required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(
        'res.currency', string="Moneda", default=lambda self: self.env.user.company_id.currency_id)
    serie = fields.Char(string='Serie', required=True, tracking=True)
    monto = fields.Monetary(string="Monto", required=True, tracking=True)
    correo_enviado = fields.Boolean(string="Correo enviado", default=False, copy=False, tracking=True)
    mail_id = fields.Many2one('mail.mail', string="Correo", copy=False, tracking=True)

    @api.model
    def eliminarRegistros(self):
        for i in self:
            i.unlink()

    @api.model
    def sincronizar_registros(self, data):
        """
        Método que se encarga de recibir los datos del control de pago a través de XMLRPC
        """
        # Instanciamos el objeto de logs
        sync_log_obj = self.env['pbp.sincronizacion_logs'].sudo().create(
            {"tipo_sincronizacion": 'Liquidaciones'})
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
                self.guardar_liquidaciones(d, sync_log_obj)

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar proformas")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_liquidaciones(self, liquidacion, sync_log_obj):
        """
        Formatear los datos de la liquidacion y guardarlos en la tabla
        """
        try:
            id_pbp = liquidacion['id_pbp']
            moneda_id = liquidacion['moneda_id']
            fecha_vencimiento = liquidacion['fecha_vencimiento']
            serie = liquidacion['serie']
            monto = liquidacion['monto']
            cliente_id = liquidacion['cliente_id']

            if moneda_id == 2:
                # currency_name = 'USD'
                currency_id = 2
            elif moneda_id == 1:
                # currency_name = 'PYG'
                currency_id = 155
            else:
                return False


            partner_id = False
            partners = self.env['res.partner'].search([('id_cliente_pbp', '=', cliente_id)])
            partner = partners[0] if partners else False
            if partner:
                partner_ruc = partner['vat']
                partner_ids = self.env['res.partner'].search([('ruc', '=', partner_ruc)])
                if len(partner_ids) > 1:
                    max_total = 0
                    for pid in partner_ids:
                        partner_novedades_total = len(self.env['pbp.novedades'].search([('partner_id', '=', pid.id)]))
                        if partner_novedades_total > max_total:
                            beneficiario_id = pid.id
                            max_total = partner_novedades_total
                    if not max_total:
                        partner_id = partner['id']
                else:
                    partner_id = partner['id']

            obj = {
                'id_pbp': id_pbp,
                'currency_id': currency_id,
                'cliente_id': cliente_id,
                'partner_id': partner_id,
                'monto': monto,
                'fecha_vencimiento': fecha_vencimiento,
                'serie': serie,
            }

            if not partner_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': liquidacion,
                        'error_msg': "No se encuentra el cliente %s" % cliente_id,
                    }
                )
            else:
                self.env['pbp.liquidaciones'].sudo().create(obj)
        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': liquidacion,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()

