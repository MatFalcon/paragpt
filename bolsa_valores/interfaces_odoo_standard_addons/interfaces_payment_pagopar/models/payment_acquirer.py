from odoo import models,api,fields,exceptions
import hashlib
import datetime
import json

class PaymentAcquirerPagopar(models.Model):
    _inherit = 'payment.acquirer'

    pagopar_private_key=fields.Char(string="Clave privada")
    pagopar_public_key=fields.Char(string="Clave pública")
    provider=fields.Selection(selection_add=[('pagopar','Pagopar')], ondelete={"pagopar": "set default"})
    envio_flete = fields.Boolean('Flete', default=False)

    def pagopar_get_form_action_url(self):
        self.ensure_one()
        return '/payment/pagopar/loadform'


    def pagopar_form_generate_values(self, values):
        base_url = self.get_base_url()
        reference = values.get('reference')
        order = self.env['sale.order'].search([('name','=',reference)])
        if "-" in reference and not order:
            reference = reference.split("-")
            order = self.env['sale.order'].search([('name', '=', reference[0])])
        if order:
          vals = json.loads(order.sudo().getPagoparFormValues())
            #'pagopar_return': urls.url_join(base_url, PagoparController._return_url),
            #'notify_url': urls.url_join(base_url, PagoparController._notify_url),
            #'cancel_return': urls.url_join(base_url, PagoparController._cancel_url),
            #})
        return vals