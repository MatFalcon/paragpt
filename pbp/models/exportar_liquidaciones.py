import datetime

from odoo import models, fields, api, exceptions

from odoo.addons.pbp.facturas.asientos import generar_asientos
from datetime import date, datetime, timedelta


class ExportarLiquidaciones(models.Model):
    _name = 'pbp.exportar_liquidaciones'
    _order = 'fecha desc'
    _rec_name = 'id'

    cuenta_debito = fields.Char(string="1-Cta debito", required=False)
    cuenta_credito = fields.Char(string="2-Cta credito", required=False)
    codigo_banco = fields.Char(string="3-Código de banco", required=False)
    currency_id = fields.Many2one('res.currency', required=False, string="4-Moneda")
    tipo_documento = fields.Char(string="5-Tipo de documento", required=False)
    nro_documento = fields.Char(string="6-Nro de documento", required=False)
    titular_cuenta = fields.Char(string="7-Titular de la cuenta", required=False)
    fecha = fields.Date(required=True, string='8-Fecha de proceso o agentamiento')
    monto = fields.Float(string="9-Monto", required=True)
    motivo = fields.Char(string="10-Motivo de la transferencia", required=True, default="Pago de Intereses")
    email = fields.Char(string="11-Email", required=False)
    sms = fields.Char(string="12-SMS", required=True, default="Pago de Intereses")
    nro_pago = fields.Char(string="13-Nro. de Pago", required=False)
    nro_factura = fields.Char(string="14-Nro. de Factura", required=False)
    txt_copiar = fields.Char(string="TXT a copiar", compute="computeTxtCopiar")

    liquidacion_id = fields.Many2one('pbp.liquidaciones', string="Liquidaciones")
    reporto_id = fields.Many2one('pbp.reporto', string="Reporto")
    control_pagos_id = fields.Many2one('pbp.control_pagos', string="Control de Pagos")
    compensacion_id = fields.Many2one('pbp.compensacion_rueda_anterior', string="Compensación de Rueda Anterior")

    def computeTxtCopiar(self):
        for i in self:
            if i.cuenta_debito:
                cuenta_debito = '"' + str(i.cuenta_debito) +'"'
            else:
                cuenta_debito = '""'
            if i.cuenta_credito:
                cuenta_credito = '"' + str(i.cuenta_credito) +'"'
            else:
                cuenta_credito = '""'
            if i.codigo_banco:
                codigo_banco = '"' + str(i.codigo_banco) +'"'
            else:
                codigo_banco = '""'
            if i.currency_id:
                moneda = '"' + str(i.currency_id.name) +'"'
            else:
                moneda = '""'
            tipo_documento = '"RUC"'
            if i.nro_documento:
                nro_documento = '"' + str(i.nro_documento) +'"'
            else:
                nro_documento = '""'
            if i.titular_cuenta:
                titular_cuenta = '"' + str(i.titular_cuenta) +'"'
            else:
                titular_cuenta = '""'
            fecha = '"' + i.fecha.strftime("%d/%m/%Y") +'"'
            monto = '"' + str(i.monto) + '"'
            motivo = '"' + str(i.motivo) + '"'
            if i.email:
                email = '"' + str(i.email) + '"'
            else:
                email = '"administracion@bolsadevalores.com.py"'
            sms = '"' + str(i.sms) + '"'
            nro_pago = '"1"'
            nro_factura = '"1"'

            i.txt_copiar = (cuenta_debito + ';' + cuenta_credito + ';' + codigo_banco + ';' + moneda + ';' +
                            tipo_documento + ';' + nro_documento + ';' + titular_cuenta + ';' + fecha + ';' + monto +
                            ';' + motivo + ';' + email + ';' + sms + ';' + nro_pago + ';' + nro_factura)