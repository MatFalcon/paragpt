# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions


class ReporteComprasXLSX(models.AbstractModel):
    _inherit = 'report.reporte_compraventa.reporte_compra_xlsx'

    def get_facturas_libro_compra(self, fecha_inicio, fecha_fin):
        result = super(ReporteComprasXLSX, self).get_facturas_libro_compra(fecha_inicio, fecha_fin)
        return result.filtered(lambda x: not x.es_factura_exterior)

    def get_exenta_5_10(self, invoice_line):
        # interfaces_iva_importacion/report/reporte_libro_compra_xlsx.py
        result = super(ReporteComprasXLSX, self).get_exenta_5_10(invoice_line)
        # result = base10, iva10, base5, iva5, exentas, imponible_importaciones
        result = list(result)
        if invoice_line.move_id.es_despacho_importacion:
            if invoice_line.account_id.es_cuenta_iva_importacion:
                result[1] = result[4]
                result[0] = result[1] * 10
                result[5] = result[0]
            result[4] = 0
        return result

    def get_proveedor(self, invoice, campo):
        # interfaces_iva_importacion/report/reporte_libro_compra_xlsx.py
        result = super(ReporteComprasXLSX, self).get_proveedor(invoice, campo)
        if invoice.es_despacho_importacion:
            proveedor_por_defecto_exterior = self.env['res.partner'].search([('es_proveedor_por_defecto_exterior', '=', True)])
            if not proveedor_por_defecto_exterior:
                raise exceptions.ValidationError('Debe de establecerse un Proveedor por defecto del Exterior para poder continuar')
            if campo == 'name':
                result = proveedor_por_defecto_exterior.name
            if campo == 'vat':
                result = proveedor_por_defecto_exterior.vat
        return result
