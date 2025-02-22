
from odoo import models, fields, api, exceptions
import logging

_logger = logging.getLogger(__name__)


class Reporto(models.Model):
    _name = 'pbp.reporto'
    _order = 'state, fecha_operacion desc'
    _rec_name = 'repo_id'

    repo_id = fields.Integer(string="Operación Mercado ID", required=True)
    fecha_operacion = fields.Date(required=True, string='Fecha')
    comitente_reportado_codigo = fields.Integer(string="Cuenta Registro Reportado", required=True)
    cod_negociacion = fields.Integer(string="Cód. Negociación", required=True)
    contrato = fields.Char(string="Contrato", required=True)
    cantidad = fields.Integer(string="Cantidad", required=True)
    precio_venta = fields.Float(string="Precio venta", required=True)
    comitente_reportador_codigo = fields.Integer(string="Cuenta Registro Reportador", required=True)
    tasa_interes = fields.Float(string="Tasa de Interés", required=True)
    plazo = fields.Integer(string="Plazo Operación", required=True)
    state = fields.Selection(
        selection=[
            ('2', 'Aceptada'),
            ('4', 'Anulada'),
            ('3', 'Rechazada'),
        ],
        required=False,
        string='Estado',
    )
    currency_id = fields.Many2one('res.currency', required=True, string="Moneda")
    monto_inicial = fields.Float(string="Monto Inicial", required=True)
    precio_recompra = fields.Float(string="Precio Re-compra", required=True)
    monto_operacion_a_termino = fields.Float(string="Monto operacion a término", required=True)
    fecha_vencimiento = fields.Date(required=True, string='Fecha de vencimiento')
    aforo = fields.Float(string="Aforo", required=False)
    tipo_repo_descripcion = fields.Char(string="Tipo Repo Descripción", required=True)
    reportador_id = fields.Many2one('res.partner', string="MC Reportador", required=True)
    reportado_id = fields.Many2one('res.partner', string="MC Reportado", required=True)
    tipo_operacion = fields.Selection(
        selection=[
            ('directa', 'Directa'),
            ('comun', 'Común')
        ],
        required=False,
        string='Tipo'
    )

    def createLine(self, cuenta_credito=None, inicial=None):
        cuenta_debito = self.env.user.company_id.partner_id.mapped('bank_ids').filtered(
            lambda x: x.cuenta_liquidaciones and x.currency_id == self.currency_id)
        email = self.reportado_id.child_ids.filtered(lambda x: x.contacto_liquidaciones).mapped(
                'email') if inicial else self.reportador_id.child_ids.filtered(lambda x: x.contacto_liquidaciones).mapped(
                'email')
        vals = {
            'cuenta_debito': cuenta_debito.acc_number if cuenta_debito else False,
            'cuenta_credito': cuenta_credito.acc_number if cuenta_credito else False,
            'codigo_banco': cuenta_credito.bank_id.bic,
            'currency_id': self.currency_id.id,
            'tipo_documento': "CI" if self.reportado_id.company_type == 'person' else "RUC",
            'nro_documento': cuenta_credito.ruc_ci,
            'titular_cuenta': cuenta_credito.acc_holder_name,
            'fecha': self.fecha_operacion if inicial else self.fecha_vencimiento,
            'monto': self.monto_inicial if inicial else self.monto_operacion_a_termino,
            'email': email[0] if len(email) > 0 else "",
            'nro_factura': "",
            'reporto_id': self.id
        }
        linea_exportacion = self.env['pbp.exportar_liquidaciones'].create(vals)

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Reporto, self).create(vals_list)
        for r in res:
            if r.contrato != '%TNA%' and r.tipo_operacion == 'comun' and r.state == '2':
                ########## REPORTADO ##########
                cuenta_reportado = r.reportado_id.mapped('bank_ids').filtered(
                    lambda x: x.cuenta_liquidaciones and x.currency_id == r.currency_id)
                if cuenta_reportado:
                    r.createLine(cuenta_credito=cuenta_reportado, inicial=True)
                ########## REPORTADOR ##########
                cuenta_reportador = r.reportador_id.mapped('bank_ids').filtered(
                    lambda x: x.cuenta_liquidaciones)
                if cuenta_reportador:
                    r.createLine(cuenta_credito=cuenta_reportador[0], inicial=False)
        return res
    
    @api.model
    def sincronizar_registros(self, data):
        """
        Método que se encarga de recibir los datos del control de pago a través de XMLRPC
        """
        # Instanciamos el objeto de logs
        sync_log_obj = self.env['pbp.sincronizacion_logs'].sudo().create(
            {"tipo_sincronizacion": 'Reporto'})
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
                self.guardar_reporto(d, sync_log_obj)

            _logger.info("Done ...")
            return True
        except Exception as e:
            _logger.error("Error al sincronizar reporto")
            _logger.error(e)

            # Si hay un error a nivel de la cabecera
            sync_log_obj.write({'error_msg': str(e), 'sincronizacion_correcta': False})

            return False

    @api.model
    def guardar_reporto(self, reporto, sync_log_obj):
        """
        Formatear los datos del reporto y guardarlos en la tabla
        """
        try:
            emisor_id = False
            receptor_id = False

            reportador_id = reporto['reportador_id']
            reportado_id = reporto['reportado_id']
            emisores = self.env['res.partner'].search([('id_cliente_pbp', '=', reportador_id)])
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

            receptores = self.env['res.partner'].search([('id_cliente_pbp', '=', reportado_id)])
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

            reportos = self.env['pbp.reporto'].search([('repo_id', '=', reporto['repo_id'])])

            reporto['reportado_id'] = receptor_id
            reporto['reportador_id'] = emisor_id

            if not emisor_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': reporto,
                        'error_msg': "No se encuentra el reportador %s" % reportador_id,
                    }
                )
            if not receptor_id:
                self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                    {
                        'sincronizacion': sync_log_obj.id,
                        'registro': reporto,
                        'error_msg': "No se encuentra el reportado %s" % reportado_id,
                    }
                )
            if receptor_id and emisor_id:
                if reportos:
                    reportos.sudo().write(reporto)
                else:
                    self.env['pbp.reporto'].sudo().create(reporto)
        except Exception as e:
            self.env['pbp.sincronizacion_detalle_logs'].sudo().create(
                {
                    'sincronizacion': sync_log_obj.id,
                    'registro': reporto,
                    'error_msg': str(e),
                }
            )
        self._cr.commit()

