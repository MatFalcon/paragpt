
# -*- coding: utf-8 -*-

import logging, hashlib, json, requests, datetime
from odoo import fields, models, api

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    token_pedido = fields.Char('Token de pedido')
    token_transaccion = fields.Char('token de la transaccion')

    flete_total = fields.Integer('Flete', compute="_getFlete")
    flete_total_materialized = fields.Float('Flete real')
    amount_total_with_flete = fields.Monetary('Total con Flete', compute="_get_total_con_flete")


    @api.depends('invoice_ids')
    @api.onchange('invoice_ids')
    def onchangeInvoice(self):
        for this in self:
            if this.token_transaccion:
                for i in this.invoice_ids:
                    i.write({'factura_web_ecommerce':True})

    def _get_total_con_flete(self):
        for order in self:
            if order.token_transaccion:
                order.amount_total_with_flete = order.amount_total + order.flete_total_materialized
            else:
                order.amount_total_with_flete = order.amount_total

    def getPagoparFormValues(self):
        base_url = self.get_base_url()
        today = fields.Datetime.now()
        date = today + datetime.timedelta(days=5)
        str_date_limit = datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S')
        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'pagopar')])
        if acquirer:
            key_privado = acquirer.pagopar_private_key
            key_publico = acquirer.pagopar_public_key
            id_pedido = str(self.id)
            monto = self.amount_total
            url_flete = "https://api.pagopar.com/api/calcular-flete/2.0/traer"

            if not self.partner_id.vat:
                ruc = "44444401-7"
                cliente_name = "Importe Consolidado"

            else:
                ruc = self.partner_id.vat
                cliente_name = self.partner_id.name

            token_flete = hashlib.sha1(key_privado.encode('utf-8') + ('CALCULAR-FLETE').encode('utf-8')).hexdigest()

            compras_items_array = []
            for line in self.order_line:
                if line.product_id.weight:
                    peso = str(line.product_id.weight)
                else:
                    peso = "0.5"
                if line.product_id.alto:
                    alto = str(line.product_id.alto)
                else:
                    alto = "10"
                if line.product_id.ancho:
                    ancho = line.product_id.ancho
                else:
                    ancho = "10"
                if line.product_id.largo:
                    largo = str(line.product_id.largo)
                else:
                    largo = "10"
                n = {
                    "ciudad": self.partner_shipping_id.city_id.id_pagopar,
                    "nombre": line.product_id.name,
                    "cantidad": line.product_uom_qty,
                    "categoria": "979",
                    "public_key": key_publico,
                    "url_imagen": base_url + "web/image/product.template/" + str(
                        line.product_id.id) + "/image",
                    "descripcion": line.product_id.name,
                    "id_producto": line.product_id.id,
                    "precio_total": line.price_total,
                    "vendedor_telefono": "",
                    "vendedor_direccion": str(self.company_id.street) + " " + str(self.company_id.street2),
                    "vendedor_direccion_referencia": "",
                    "vendedor_direccion_coordenadas": "",
                    "peso": peso,
                    "largo": largo,
                    "ancho": ancho,
                    "alto": alto
                }
                compras_items_array.append(n)

            flete_1 = {"tipo_pedido": "VENTA-COMERCIO",
                       "fecha_maxima_pago": str_date_limit,
                       "public_key": key_publico,
                       "id_pedido_comercio": id_pedido,
                       "monto_total": int(monto),
                       # "monto_total": 1000,
                       "token": token_flete,
                       "descripcion_resumen": "Compra de productos/servicios",
                       "comprador": {
                           "ruc": ruc,
                           "email": self.partner_invoice_id.email,
                           "ciudad": self.partner_shipping_id.city_id.id_pagopar,
                           # "ciudad":"1",
                           "nombre": cliente_name,
                           "telefono": self.partner_invoice_id.phone,
                           "direccion": str(self.partner_shipping_id.street) + " " + str(self.partner_shipping_id.street2),
                           "direccion_referencia": "",
                           "coordenadas": "",
                           "documento": ruc.split('-')[0],
                           "razon_social": cliente_name,
                           "tipo_documento": "CI"},
                       "compras_items": compras_items_array,
                       "token_publico": key_publico
                       }

            flete_response_1_json = requests.post(url_flete, data=json.dumps(flete_1))

            flete_response_1 = json.loads(flete_response_1_json.text)

            if flete_response_1.get('compras_items'):
                for i in flete_response_1.get('compras_items'):
                    for o in i['opciones_envio']['metodo_aex']['opciones']:
                        if o['id'] == '3-0':
                            costo = o['costo']
                    i['opciones_envio']['metodo_aex']['costo'] = costo
                    i['opciones_envio']['metodo_aex']['id'] = '3-0'
                    i['envio_seleccionado'] = "aex"
                    i['costo_envio'] = costo
                    flete_response_1['monto_total'] = flete_response_1['monto_total'] + costo

                json_flete_2 = json.dumps(flete_response_1)

                flete_response_2_json = requests.post(url_flete, data=json_flete_2)

                flete_response_2 = json.loads(flete_response_2_json.text)

                token_transaccion = hashlib.sha1(key_privado.encode('utf-8') + str(id_pedido).encode('utf-8') + str(
                    flete_response_2['monto_total']).encode('utf-8')).hexdigest()

                flete_response_2['token'] = token_transaccion
                return json.dumps(flete_response_2)

    def _getFlete(self):
        base_url = self.get_base_url()
        today = fields.Datetime.now()
        date = today + datetime.timedelta(days=5)
        str_date_limit = datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S')

        acquirer = self.env['payment.acquirer'].search([('provider', '=', 'pagopar')])
        if acquirer:
            key_privado = acquirer.pagopar_private_key
            key_publico = acquirer.pagopar_public_key
            id_pedido = str(self.id)
            monto = self.amount_total
            print(self.amount_tax)
            print(self.amount_total)
            url_flete = "https://api.pagopar.com/api/calcular-flete/2.0/traer"

            if not self.partner_id.vat:
                ruc = "44444401-7"
                cliente_name = "Importe Consolidado"

            else:
                ruc = self.partner_id.vat
                cliente_name = self.partner_id.name

            token_flete = hashlib.sha1(key_privado.encode('utf-8') + ('CALCULAR-FLETE').encode('utf-8')).hexdigest()

            compras_items_array = []
            for line in self.order_line:
                if line.product_id.weight:
                    peso = str(line.product_id.weight)
                else:
                    peso = "0.5"
                if line.product_id.alto:
                    alto = str(line.product_id.alto)
                else:
                    alto = "10"
                if line.product_id.ancho:
                    ancho = line.product_id.ancho
                else:
                    ancho = "10"
                if line.product_id.largo:
                    largo = str(line.product_id.largo)
                else:
                    largo = "10"
                n = {
                    "ciudad": self.partner_shipping_id.city_id.id_pagopar,
                    "nombre": line.product_id.name,
                    "cantidad": line.product_uom_qty,
                    "categoria": "979",
                    "public_key": key_publico,
                    "url_imagen": base_url + "web/image/product.template/" + str(
                        line.product_id.id) + "/image",
                    "descripcion": line.product_id.name,
                    "id_producto": line.product_id.id,
                    "precio_total": line.price_total,
                    "vendedor_telefono": "",
                    "vendedor_direccion": str(self.company_id.street) + " " + str(self.company_id.street2),
                    "vendedor_direccion_referencia": "",
                    "vendedor_direccion_coordenadas": "",
                    "peso": peso,
                    "largo": largo,
                    "ancho": ancho,
                    "alto": alto
                }
                compras_items_array.append(n)

            flete_1 = {"tipo_pedido": "VENTA-COMERCIO",
                       "fecha_maxima_pago": str_date_limit,
                       "public_key": key_publico,
                       "id_pedido_comercio": id_pedido,
                       "monto_total": int(monto),
                       #"monto_total": 1000,
                       "token": token_flete,
                       "descripcion_resumen": "Compra de productos/servicios",
                       "comprador": {
                           "ruc": ruc,
                           "email": self.partner_invoice_id.email,
                           "ciudad": self.partner_shipping_id.city_id.id_pagopar,
                           # "ciudad":"1",
                           "nombre": cliente_name,
                           "telefono": self.partner_invoice_id.phone,
                           "direccion": str(self.partner_shipping_id.street) + " " + str(self.partner_shipping_id.street2),
                           "direccion_referencia": "",
                           "coordenadas": "",
                           "documento": ruc.split('-')[0],
                           "razon_social": cliente_name,
                           "tipo_documento": "CI"},
                       "compras_items": compras_items_array,
                       "token_publico": key_publico
                       }
            json_flete_1 = json.dumps(flete_1)

            flete_response_1_json = requests.post(url_flete, data=json_flete_1)

            flete_response_1 = json.loads(flete_response_1_json.text)

            if flete_response_1.get('compras_items'):
                for i in flete_response_1['compras_items']:
                    i['envio_seleccionado'] = "aex"
                    for o in i['opciones_envio']['metodo_aex']['opciones']:
                        if o['id'] == '3-0':
                            i['costo_envio'] = o['costo']
                            self.flete_total = o['costo']

                json_flete_2 = json.dumps(flete_response_1)

                flete_response_2_json = requests.post(url_flete, data=json_flete_2)

                flete_response_2 = json.loads(flete_response_2_json.text)

                token_transaccion = hashlib.sha1(
                    key_privado.encode('utf-8') + id_pedido.encode('utf-8') + str(
                        flete_response_2['monto_total']).encode('utf-8')).hexdigest()
                flete_response_2['token'] = token_transaccion
            else:
                _logger.fatal('\nError en la transacción\n')



