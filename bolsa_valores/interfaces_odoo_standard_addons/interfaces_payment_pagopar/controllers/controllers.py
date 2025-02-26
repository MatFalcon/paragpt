# -*- coding: utf-8 -*-
import ast

from odoo import http
import requests
import json
from odoo.http import request, route, Response, JsonRequest
from werkzeug.utils import redirect
import hashlib

from odoo import fields
from datetime import date
import webbrowser

from odoo.tools import date_utils

def alternative_json_response(self, result=None, error=None):

    if error is not None:
        response = error

    if result is not None:
        response = result

    mime = 'application/json'
    body = json.dumps(response, default=date_utils.json_default)

    return Response(
        body, status=error and error.pop('http_status', 200) or 200,
        headers=[('Content-Type', mime), ('Content-Length', len(body))]
    )


class InterfacesPaymentPagopar(http.Controller):

    @http.route('/pagopar/resultado/<string:hash>', auth='public', methods=['GET'], type='http', csrf=False)
    def resultado_pago(self, **post):
        acquirer = request.env['payment.acquirer'].search([('provider','=','pagopar')])
        if acquirer:
            token_publico = acquirer.pagopar_public_key
            token_privado = acquirer.pagopar_private_key
            values = dict(post)
            token = hashlib.sha1((token_privado).encode('utf-8') + ("CONSULTA").encode('utf-8')).hexdigest()
            vals = ({
                "hash_pedido": values.get('hash'),
                "token": token,
                "token_publico": token_publico
            })

            response_json = requests.post("https://api.pagopar.com/api/pedidos/1.1/traer", data=json.dumps(vals))

            data_dict = json.loads(response_json.text)

            if data_dict['respuesta']:

                pedido = request.env['sale.order'].sudo().search(
                    [('token_transaccion', '=', data_dict['resultado'][0]['hash_pedido'])])

                if pedido:
                    if pedido.state not in ['done','cancel']:
                        pedido.action_confirm()

                    transaction = request.env['payment.transaction'].sudo().search([('sale_order_ids', 'in', pedido.id)])

                    transaction.sudo().update({
                        'state_message': data_dict['resultado'][0]['forma_pago'] + ' ' + data_dict['resultado'][0][
                            'monto'] + ' ' + data_dict['resultado'][0]['token']
                    })
                    if data_dict['resultado'][0]['pagado'] == True:
                        transaction.sudo().update({'state': 'done'})
                        if pedido.state not in ['done','cancel'] and pedido.invoice_status == 'to invoice':
                            move = pedido.sudo()._create_invoices()
                            move.sudo().action_post()
                        transaction.sudo()._reconcile_after_done()

                    else:
                        transaction.sudo().update({'state': 'pending'})

            return request.redirect('/payment/status')



    @http.route('/pagopar/confirmacion_pago/', auth='public', methods=['POST'], type='json', csrf=False)
    def confirmacion_pago(self, **post):
        data1 = request.httprequest.data
        my_json = data1.decode('utf8').replace("'", '"')
        data_dict = json.loads(my_json)
        if data_dict['respuesta']:

            pedido = request.env['sale.order'].sudo().search(
                [('token_transaccion', '=', data_dict['resultado'][0]['hash_pedido'])])

            if pedido:
                if pedido.state not in ['done','cancel']:
                    pedido.action_confirm()

                transaction = request.env['payment.transaction'].sudo().search([('sale_order_ids', 'in', pedido.id)])

                transaction.sudo().update({
                    'state_message': data_dict['resultado'][0]['forma_pago'] + ' ' + data_dict['resultado'][0][
                        'monto'] + ' ' + data_dict['resultado'][0]['token']
                })
                if data_dict['resultado'][0]['pagado'] == True:
                    transaction.sudo().update({'state': 'done'})
                    if pedido.state not in ['done','cancel'] and pedido.invoice_status == 'to invoice':
                        move = pedido.sudo()._create_invoices()
                        move.sudo().action_post()
                    transaction.sudo()._reconcile_after_done()
                else:
                    transaction.sudo().update({'state': 'pending'})


        request._json_response = alternative_json_response.__get__(request, JsonRequest)
        return [data_dict['resultado'][0]]


    @http.route('/payment/pagopar/loadform/', auth='user',csrf=False, website=True)
    def index(self, **kw):
        print('llega aca')
        order = request.env['sale.order'].sudo().browse(int(kw.get('id_pedido_comercio')))
        vals = json.loads(order.sudo().getPagoparFormValues())
        compras_items = vals.get(('compras_items'))
        for i in compras_items:
            for o in i['opciones_envio']['metodo_aex']['opciones']:
                if o['id'] == '3-0':
                    costo = o['costo']
            i['opciones_envio']['metodo_aex']['costo'] = costo
            i['opciones_envio']['metodo_aex']['id'] = '3-0'
            i['envio_seleccionado'] = "aex"
            i['costo_envio'] = costo
        vals = {"tipo_pedido": "VENTA-COMERCIO",
                "fecha_maxima_pago": vals.get('fecha_maxima_pago'),
                "public_key": vals.get('public_key'),
                "id_pedido_comercio": vals.get('id_pedido_comercio'),
                "monto_total": int(vals.get('monto_total')),
                "token":vals.get('token'),
                "descripcion_resumen": "Compra de prueba",
                "comprador": (vals.get('comprador')),
                "compras_items": compras_items,
                }
        res_json=json.dumps(vals)
        response=requests.post("https://api.pagopar.com/api/comercios/2.0/iniciar-transaccion",res_json)
        data=json.loads(response.text)
        if data.get('respuesta') is not None:
            resultado = data.get('resultado')
            if isinstance(resultado[0], dict):
                token = resultado[0].get('data')
                order.write({'token_transaccion':token})
                token = 'https://www.pagopar.com/pagos/' + token
                response = redirect(token)
                return response
            else:
                return http.request.render("interfaces_payment_pagopar.error_pago", {'resultado': resultado,'order':order})
        else:
            token = data.get('resultado')
            return
