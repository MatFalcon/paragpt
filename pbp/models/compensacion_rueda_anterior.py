import logging

from odoo import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class CompensacionRuedaAnterior(models.Model):
    _name = 'pbp.compensacion_rueda_anterior'
    _order = 'fecha desc'
    _rec_name = 'id'

    #id_pbp = fields.Integer(string="Repo ID", required=True)
    fecha = fields.Date(required=True, string='Fecha')
    beneficiario_id = fields.Many2one('res.partner', string="Beneficiario", required=True)
    cuenta_usd = fields.Char(string="Cuenta USD", required=False)
    cuenta_gs = fields.Char(string="Cuenta GS", required=False)
    importe_gs = fields.Float(string="Importe GS", required=False)
    importe_usd = fields.Float(string="Importe USD", required=False)
    segmento_mercado = fields.Selection(
        selection=[
            ('Primario', 'Primario'),
            ('Secundario', 'Secundario')
        ],
        required=False,
        string='Segmento de Mercado',
    )
    tcero= fields.Boolean(string="T+0", default=True)
    active = fields.Boolean(string="Activo", default=True)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(CompensacionRuedaAnterior, self).create(vals_list)
        for r in res:
            if r.tcero:
                compensacion = self.env['pbp.compensacion_rueda_anterior'].search([('fecha','=',r.fecha),
                                                                                   ('tcero','=',False),
                                                                                   ('beneficiario_id','=',r.beneficiario_id.id),
                                                                                   ('importe_gs','=',r.importe_gs),
                                                                                   ('importe_usd','=',r.importe_usd)])
                if compensacion:
                    compensacion.write({'active':False})
            elif (r.importe_gs > 0 or r.importe_usd > 0) and r.beneficiario_id.id_cliente_pbp != 37:
                if r.importe_usd > 0:
                    currency_id = 2
                elif r.importe_gs > 0:
                    currency_id = 155
                cuenta_debito = self.env.user.company_id.partner_id.mapped('bank_ids').filtered(lambda x:x.cuenta_liquidaciones and
                                                                                                         x.currency_id.id == currency_id)
                cuenta_credito = r.beneficiario_id.mapped('bank_ids').filtered(lambda x:x.cuenta_liquidaciones and
                                                                                        x.currency_id.id == currency_id)
                email = r.beneficiario_id.child_ids.filtered(lambda x: x.contacto_liquidaciones).mapped('email')
                vals = {
                    'cuenta_debito': cuenta_debito[0].acc_number if cuenta_debito else False,
                    'cuenta_credito': cuenta_credito[0].acc_number if cuenta_credito else False,
                    'codigo_banco': cuenta_credito[0].bank_id.bic if cuenta_credito else False,
                    'currency_id': currency_id,
                    'tipo_documento': "CI" if r.beneficiario_id.company_type == 'person' else "RUC",
                    'nro_documento': cuenta_credito[0].ruc_ci if cuenta_credito else False,
                    'titular_cuenta': cuenta_credito[0].acc_holder_name if cuenta_credito else False,
                    'fecha': r.fecha,
                    'monto': r.importe_gs if r.importe_gs > 0 else r.importe_usd,
                    'email': email[0] if len(email) > 0 else "",
                    'nro_factura': "",
                    'compensacion_id': r.id
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
            {"tipo_sincronizacion": 'Compensación de Rueda Anterior'})
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
                self.guardar_compensacion_rueda_anterior(d, sync_log_obj)

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar proformas")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_compensacion_rueda_anterior(self, compensacion_rueda_anterior, sync_log_obj):
        """
        Formatear los datos de la compensacion de rueda anterior y guardarlos en la tabla
        """
        try:
            beneficiario_id_sis = compensacion_rueda_anterior['beneficiario_id']
            importe_gs = compensacion_rueda_anterior['importe_gs']
            importe_usd = compensacion_rueda_anterior['importe_usd']
            cuenta_gs = compensacion_rueda_anterior['cuenta_gs']
            cuenta_usd = compensacion_rueda_anterior['cuenta_usd']
            segmento_mercado = compensacion_rueda_anterior['segmento_mercado']
            fecha = compensacion_rueda_anterior['fecha']


            beneficiario_id = False
            beneficiarios = self.env['res.partner'].search([('id_cliente_pbp', '=', beneficiario_id_sis)])
            beneficiario = beneficiarios[0] if beneficiarios else False
            if beneficiario:
                partner_ruc = beneficiario['vat']
                partner_ids = self.env['res.partner'].search([('vat', '=', partner_ruc)])
                if len(partner_ids) > 1:
                    max_total = 0
                    for pid in partner_ids:
                        beneficiario_novedades_total = len(self.env['pbp.novedades'].search([('partner_id', '=', pid.id)]))
                        if beneficiario_novedades_total > max_total:
                            beneficiario_id = pid.id
                            max_total = beneficiario_novedades_total
                    if not max_total:
                        beneficiario_id = beneficiario['id']
                else:
                    beneficiario_id = beneficiario['id']

            compensaciones = self.env['pbp.compensacion_rueda_anterior'].search([('beneficiario_id', '=', beneficiario_id),
                                                                                 ('fecha', '=', fecha),
                                                                                 ('segmento_mercado', '=', segmento_mercado),
                                                                                 ('importe_gs', '=', importe_gs),
                                                                                 ('importe_usd', '=', importe_usd)])

            obj = {
                'beneficiario_id': beneficiario_id,
                'fecha': fecha,
                'importe_gs': importe_gs,
                'importe_usd': importe_usd,
                'cuenta_usd': cuenta_usd,
                'cuenta_gs': cuenta_gs,
                'segmento_mercado': segmento_mercado,
                'tcero': False
            }

            if not beneficiario_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': compensacion_rueda_anterior,
                        'error_msg': "No se encuentra el beneficiario %s" % beneficiario_id_sis,
                    }
                )
            else:
                if compensaciones:
                    compensaciones.sudo().write(obj)
                else:
                    self.env['pbp.compensacion_rueda_anterior'].sudo().create(obj)
        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': compensacion_rueda_anterior,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()