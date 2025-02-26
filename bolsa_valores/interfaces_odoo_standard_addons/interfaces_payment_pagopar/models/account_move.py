
# -*- coding: utf-8 -*-

import logging, hashlib, json, requests, datetime
from odoo import fields, models, api,exceptions

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    factura_web_ecommerce = fields.Boolean('Factura Web Ecommerce', default=False)
    reversado = fields.Boolean('Reversado', default=False)
    tiempo_reversion = fields.Char('Tiempo de reversion')

    def button_reversar(self):
        for i in self:
            order = self.env['sale.order'].search([('invoice_ids','=', i.id),('token_transaccion','!=',False)])
            acquirer = self.env['payment.acquirer'].search([('provider', '=', 'pagopar')])
            if order and acquirer:
                key_privado = acquirer.pagopar_private_key
                key_publico = acquirer.pagopar_public_key
                url_flete = "https://api.pagopar.com/api/pedidos/1.1/reversar"
                token_reversar = hashlib.sha1(key_privado.encode('utf-8') + ('PEDIDO-REVERSAR').encode('utf-8')).hexdigest()

                data = {"hash_pedido": order.token_transaccion,
                           "token": token_reversar,
                           "token_publico": key_publico,
                           }

                reversar_response_1_json = requests.post(url_flete, data=json.dumps(data))

                reversar_response_1 = json.loads(reversar_response_1_json.text)

                if reversar_response_1.get('respuesta'):
                    if not reversar_response_1['respuesta']:
                        raise exceptions.ValidationError(
                            'No se ha podido reversar el pago. Favor comunicarse a reversiones@pagopar.com')
                    else:
                        if reversar_response_1['resultado'][0]['tiempo_reversion'] == 'Inmediata':
                            i.tiempo_reversion = 'Inmediata'
                        else:
                            i.tiempo_reversion = 'Agendada'
                        order.action_cancel()
                        i.button_draft()
                        #i.button_cancel()
                        i.reversado = True