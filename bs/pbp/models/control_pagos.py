import datetime
import logging
from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class ControlPagos(models.Model):
    _name = 'pbp.control_pagos'
    _order = 'emisor_id asc'
    _rec_name = 'id'

    # id_pbp = fields.Integer(string="Repo ID", required=True)
    fecha = fields.Date(required=True, string='Fecha')
    emisor_id = fields.Many2one('res.partner', string="Emisor", required=True)
    miembro_compensador_id = fields.Many2one('res.partner', string="Beneficiario", required=True)
    currency_id = fields.Many2one('res.currency', required=True, string="Moneda")
    importe_pyg = fields.Float(string="Importe PYG", required=False)
    importe_usd = fields.Float(string="Importe USD", required=False)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(ControlPagos, self).create(vals_list)
        for r in res:
            if (r.importe_pyg > 0 or r.importe_usd > 0) and r.emisor_id.id_cliente_pbp != 37:
                if r.importe_usd > 0:
                    currency_id = 2
                elif r.importe_pyg > 0:
                    currency_id = 155
                cuenta_debito = self.env.user.company_id.partner_id.mapped('bank_ids').filtered(
                    lambda x: x.cuenta_liquidaciones and x.currency_id.id == currency_id)
                cuenta_credito = r.miembro_compensador_id.mapped('bank_ids').filtered(lambda x: x.cuenta_liquidaciones
                                                                                                and x.currency_id.id == currency_id)
                email = r.miembro_compensador_id.child_ids.filtered(lambda x: x.contacto_liquidaciones).mapped('email')
                vals = {
                    'cuenta_debito': cuenta_debito.acc_number if cuenta_debito else False,
                    'cuenta_credito': cuenta_credito.acc_number if cuenta_credito else False,
                    'codigo_banco': cuenta_credito.bank_id.bic,
                    'currency_id': currency_id,
                    'tipo_documento': "CI" if r.miembro_compensador_id.company_type == 'person' else "RUC",
                    'nro_documento': cuenta_credito.ruc_ci,
                    'titular_cuenta': cuenta_credito.acc_holder_name,
                    'fecha': r.fecha,
                    'monto': r.importe_pyg if r.importe_pyg > 0 else r.importe_usd,
                    'email': email[0] if len(email) > 0 else "",
                    'nro_factura': "",
                    'control_pagos_id': r.id
                }
                linea_exportacion = self.env['pbp.exportar_liquidaciones'].create(vals)
        return res

    @api.model
    def sincronizar_registros(self, data):
        """
        Método que se encarga de recibir los datos del control de pago a través de XMLRPC
        """
        # Instanciamos el objeto de logs
        sync_log_obj = self.env['pbp.sincronizacion_logs'].sudo().create(
            {"tipo_sincronizacion": 'Control de Pago'})
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
                self.guardar_control_pago(d, sync_log_obj)

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar proformas")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_control_pago(self, control_pago, sync_log_obj):
        """
        Formatear los datos del control de pago y guardarlos en la tabla
        """
        try:
            emisor_id_sis = control_pago['emisor_id_sis']
            miembro_compensador_id_sis = control_pago['miembro_compensador_id_sis']
            moneda_id = control_pago['moneda_id']
            fecha = control_pago['fecha']
            importe_usd = 0
            importe_pyg = 0
            if moneda_id == 'Dólar':
                # currency_name = 'USD'
                currency_id = 2
                importe_usd = control_pago['importe_total']
            elif moneda_id == 'Guaraní':
                # currency_name = 'PYG'
                currency_id = 155
                importe_pyg = control_pago['importe_total']
            else:
                return False

            emisor_id = False
            miembro_compensador_id = False
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

            miembros_compensadores = self.env['res.partner'].search([('id_cliente_pbp', '=', miembro_compensador_id_sis)])
            miembro_compensador = miembros_compensadores[0] if miembros_compensadores else False
            if miembro_compensador:
                partner_ruc = miembro_compensador['vat']
                partner_ids = self.env['res.partner'].search([('vat', '=', partner_ruc)])
                if len(partner_ids) > 1:
                    max_total = 0
                    for pid in partner_ids:
                        miembro_compensador_novedades_total = len(self.env['pbp.novedades'].search([('partner_id', '=', pid.id)]))
                        if miembro_compensador_novedades_total > max_total:
                            miembro_compensador_id = pid.id
                            max_total = miembro_compensador_novedades_total
                    if not max_total:
                        miembro_compensador_id = miembro_compensador['id']
                else:
                    miembro_compensador_id = miembro_compensador['id']

            controles = self.env['pbp.control_pagos'].search([('emisor_id', '=', emisor_id),
                                                              ('miembro_compensador_id', '=', miembro_compensador_id),
                                                              ('fecha', '=', fecha),
                                                              ('currency_id', '=', currency_id),
                                                              ('importe_usd', '=', importe_usd),
                                                              ('importe_pyg', '=', importe_pyg)])

            obj = {
                'emisor_id': emisor_id,
                'miembro_compensador_id': miembro_compensador_id,
                'fecha': fecha,
                'currency_id': currency_id,
                'importe_usd': importe_usd,
                'importe_pyg': importe_pyg
            }

            if not emisor_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': control_pago,
                        'error_msg': "No se encuentra el emisor %s" % emisor_id_sis,
                    }
                )
            if not miembro_compensador_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': control_pago,
                        'error_msg': "No se encuentra el miembro compensador %s" % miembro_compensador_id_sis,
                    }
                )
            if miembro_compensador_id and emisor_id:
                if controles:
                    controles.sudo().write(obj)
                else:
                    self.env['pbp.control_pagos'].sudo().create(obj)
        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': control_pago,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()
