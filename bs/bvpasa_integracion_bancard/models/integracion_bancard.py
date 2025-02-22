# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
import requests
import pandas as pd
import csv
import datetime
import xlrd
from base64 import b64decode


class IntegracionBancard(models.Model):
    _name = 'bvpasa_integracion_bancard'
    _description = "Integración con Bancard"
    _rec_name = "nro_transaccion"


    nro_transaccion = fields.Char(string="Nro de Transaccion")
    tipo_tarjeta = fields.Char(string="Tipo de Tarjeta")
    currency_id = fields.Many2one('res.currency', string="Moneda")
    importe = fields.Float(string="Importe")
    tipo = fields.Char(string="Tipo")
    estado = fields.Char(string="Estado")
    monto_comision = fields.Float(string="Monto Comisión")
    iva_s_comision = fields.Float(string="IVA sin comisión")
    retencion_renta = fields.Float(string="Retención Renta")
    retencion_iva = fields.Float(string="Retención IVA")
    importe_neto = fields.Float(string="Importe Neto")
    fecha_venta = fields.Datetime(string="Fecha de Venta")
    fecha_credito_comercio = fields.Date(string="Fecha de Crédito del Comercio")
    invoice_id = fields.Many2one('account.move', string="Factura")
    campus_id = fields.Many2one('bvpasa_integracion_campus',string="Campus")

    def obtenerReportes(self):
        url = self.env['ir.config_parameter'].get_param('bancard_url')
        password = self.env['ir.config_parameter'].get_param('bancard_private_key')
        username = self.env['ir.config_parameter'].get_param('bancard_public_key')
        file_path = self.env['ir.config_parameter'].get_param('bancard_file_path')

        url = url + '?from_date=2023-12-19'

        response = requests.get(url, auth=(username, password))

        if response.status_code == 200:
            res = response.json()
            lines = res['automatic_reports']
            for l in lines:
                file_url = l['url']
                file = requests.get(file_url)
                file_final = open(file_path, 'wb')
                file_final.write(file.content)
                file_final.close()
                #file_final = open('/home/silvana/Documents/addons_customers/bvpasa_odoo_addons/reporte_bancard.csv', 'wb')
                #file_final.close()
                with open(file_path, newline='', encoding='latin-1') as csvfile:
                    reader = csv.reader(csvfile, delimiter=';')
                    c = 0
                    for row in reader:
                        if c != 0:
                            moneda = self.env['res.currency'].search([('name', '=', str(row[10]))]).id
                            fecha_venta = datetime.datetime.strptime(str(row[0]), '%d/%m/%Y %H:%M')
                            fecha_credito_comercio = False
                            if str(row[36]):
                                fecha_credito_comercio = datetime.datetime.strptime(str(row[36]), '%Y-%m-%d')
                            line = {
                                'fecha_venta': fecha_venta,
                                # 'fecha_anulada': str(row[1]),
                                'nro_transaccion': str(row[2]),
                                'tipo_tarjeta': str(row[3]),
                                # 'codigo_autorizacion': str(row[4]),
                                # 'emisor': str(row[5]),
                                # 'nro_tarjeta': str(row[6]),
                                # 'marca': str(row[7]),
                                # 'cuotas': str(row[8]),
                                # 'plan_pago': str(row[9]),
                                'currency_id': moneda,
                                'importe': str(row[11]),
                                # 'sexo': str(row[12]),
                                # 'fecha_nacimiento': self.convertir_fecha(row[13], row),
                                # 'cod_sucursal': str(row[14]),
                                # 'sucursal': str(row[15]),
                                # 'origen': str(row[16]),
                                'tipo': str(row[17]),
                                # 'dispositivo': str(row[18]),
                                'estado': str(row[20]),
                                # 'codigo_iata': str(row[20]),
                                # 'comision_td': str(row[21]),
                                # 'tipo_servicio': str(row[22]),
                                # 'prestacion': str(row[23]),
                                # 'producto': str(row[24]),
                                # 'afinidad': str(row[25]),
                                # 'nro_resumen': str(row[26]),
                                'monto_comision': str(row[28]),
                                'iva_s_comision': str(row[29]),
                                'retencion_renta': str(row[30]),
                                'retencion_iva': str(row[31]),
                                'importe_neto': str(row[32]),
                                # 'codigo_cuenta_entidad_deposito': str(row[32]),
                                # 'nro_cuenta_banco': str(row[33]),
                                # 'porcentaje_comision_comercio': str(row[34]),
                                'fecha_credito_comercio': fecha_credito_comercio,
                                # 'fecha_promocion': str(row[36]),
                                # 'caja': str(row[37]),
                                # 'servicio_transaccion': str(row[38]),
                                # 'descripcion_servicio': str(row[39]),
                                # 'prestacion2': str(row[40]),
                                # 'descripcion_prestacion': str(row[41]),
                                # 'datos_adicionales': str(row[42])
                            }
                            line_anterior = self.env['bvpasa_integracion_bancard'].search([('nro_transaccion','=',str(row[2]))])
                            if line_anterior:
                                line_anterior.write(line)
                            else:
                                self.env['bvpasa_integracion_bancard'].create(line)
                        c = c + 1


    @api.model
    def FacturarCoincidentes(self):
        r_bancard = self.env['bvpasa_integracion_bancard'].search([('invoice_id','=',False)])
        r_campus = self.env['bvpasa_integracion_campus'].search([('invoice_id','=',False)])
        for b in r_bancard:
            c = r_campus.filtered(lambda x:x.ticket_number == b.nro_transaccion)
            for ci in c:
                lines = []
                analytic_account_id = self.env['account.analytic.account'].search([('name','=','CES')])
                ci.write({'bancard_id': b.id})
                b.write({'campus_id': ci.id})
                for curso in ci.curso_ids:
                    lines.append((0, 0, {
                        'currency_id': b.currency_id,
                        'product_id': curso.product_id.id,
                        'quantity':1,
                        'price_unit': ci.monto,
                        'account_id': curso.product_id.property_account_income_id.id,
                        'analytic_account_id': analytic_account_id.id if analytic_account_id else False,
                        'tax_ids': [(6, 0, curso.product_id.taxes_id.ids)],
                    }))

                cabecera = {
                    'currency_id': b.currency_id.id,
                    'date': b.fecha_venta,
                    # 'journal_id':
                    'move_type': 'out_invoice',
                    'invoice_date': b.fecha_venta,
                    'partner_id': ci.partner_id.id,
                    'invoice_line_ids': lines,
                    'invoice_date_due': b.fecha_credito_comercio,
                    'payment_reference': b.nro_transaccion[:7]
                }
                factura = self.env['account.move'].create(cabecera)
                factura.action_post()
                ci.write({'invoice_id': factura.id})
                b.write({'invoice_id': factura.id})
