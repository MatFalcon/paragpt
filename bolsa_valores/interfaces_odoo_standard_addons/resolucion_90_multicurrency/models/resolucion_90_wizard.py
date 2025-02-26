# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Resolucion90Wizard(models.Model):
    _inherit = 'resolucion_90.wizard'

    currency_id = fields.Many2one('res.currency', string='Moneda', default=lambda self: self.env.company.currency_id, required=True)

    @api.model
    def obtener_valores_ventas(self, facturas):
        valores = []

        for i in facturas:
            reg = {
                'o1': 1,
                'o2': i.get_tipo_identificacion(),
                'o3': i.get_identificacion(),
                'o4': i.get_nombre_partner(),
                'o5': i.get_tipo_comprobante(),
                'o6': i.get_fecha_comprobante(),
                'o7': i.get_timbrado(),
                'o8': i.get_numero_comprobante(),
                'o9': i.get_monto10(self.currency_id),
                'o10': i.get_monto5(self.currency_id),
                'o11': i.get_monto_exento(self.currency_id),
                'o12': i.get_monto_total(self.currency_id),
                'o13': i.get_condicion_venta(),
                'o14': i.get_operacion_moneda_extranjera(),
                'o15': i.get_imputa_iva(),
                'o16': i.get_imputa_ire(),
                'o17': i.get_imputa_irp_rsp(),
                'o18': i.get_nro_comprobante_asociado(),
                'o19': i.get_timbrado_comprobante_asociado()
            }
            valores.append(reg)
        valores_archivo = ''
        for val in valores:
            valores_archivo = valores_archivo + "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                val.get('o1'), val.get('o2'), val.get('o3'), val.get('o4'), val.get('o5'), val.get('o6'), val.get(
                    'o7'), val.get('o8'), val.get('o9'), val.get('o10'), val.get('o11'), val.get('o12'), val.get('o13'), val.get('o14'), val.get('o15'),
                val.get('o16'), val.get('o17'), val.get('o18'), val.get('o19'))

        return valores_archivo

    @api.model
    def obtener_valores_compras(self, facturas):
        valores = []

        for i in facturas:
            reg = {
                'o1': 2,
                'o2': i.get_tipo_identificacion(),
                'o3': i.get_identificacion(),
                'o4': i.get_nombre_partner(),
                'o5': i.get_tipo_comprobante(),
                'o6': i.get_fecha_comprobante(),
                'o7': i.get_timbrado(),
                'o8': i.get_numero_comprobante(),
                'o9': i.get_monto10(self.currency_id),
                'o10': i.get_monto5(self.currency_id),
                'o11': i.get_monto_exento(self.currency_id),
                'o12': i.get_monto_total(self.currency_id),
                'o13': i.get_condicion_venta(),
                'o14': i.get_operacion_moneda_extranjera(),
                'o15': i.get_imputa_iva(),
                'o16': i.get_imputa_ire(),
                'o17': i.get_imputa_irp_rsp(),
                'o18': i.get_no_imputa(),
                'o19': i.get_nro_comprobante_asociado(),
                'o20': i.get_timbrado_comprobante_asociado()
            }
            valores.append(reg)
        valores_archivo = ''
        for val in valores:
            valores_archivo = valores_archivo + "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                val.get('o1'), val.get('o2'), val.get('o3'), val.get('o4'), val.get('o5'), val.get('o6'), val.get(
                    'o7'), val.get('o8'), val.get('o9'), val.get('o10'), val.get('o11'), val.get('o12'), val.get('o13'), val.get('o14'), val.get('o15'),
                val.get('o16'), val.get('o17'), val.get('o18'), val.get('o19'), val.get('o20'))

        return valores_archivo
