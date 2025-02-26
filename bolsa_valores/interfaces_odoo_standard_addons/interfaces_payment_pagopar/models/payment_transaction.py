# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from werkzeug import urls

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment_paypal.const import PAYMENT_STATUS_MAPPING
from odoo.addons.payment_paypal.controllers.main import PaypalController
import json

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Pagopar-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """

        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != 'pagopar':
            return res


        base_url = self.acquirer_id.get_base_url()
        vals = json.loads(self.sale_order_ids[0].sudo().getPagoparFormValues())

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
                "token": vals.get('token'),
                "descripcion_resumen": "Compra de productos/servicios",
                "comprador": (vals.get('comprador')),
                "compras_items": compras_items,
                "api_url": self.acquirer_id.pagopar_get_form_action_url(),
                }

        return vals
