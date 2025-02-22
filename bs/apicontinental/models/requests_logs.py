# -*- coding: utf-8 -*-
from odoo import api, fields, models


class RequestsLogs(models.Model):
    _name = "apicontinental.requests_logs"
    _description = "Registro de Logs de las peticiones a la API Continental"

    name = fields.Char(string="Acción", required=True)
    user = fields.Char(string="Usuario")
    url = fields.Char(string="URL")
    headers = fields.Char(string="Headers")
    payload = fields.Char(string="Payload")
    response = fields.Char(string="Respuesta")
    error = fields.Char(string="Error")
    status = fields.Integer(string="Código de respuesta")
    fecha = fields.Datetime(string="Fecha y hora", default=fields.Datetime.now)
    payment = fields.Many2one('account.payment', string="Pago")

    def save_request(self, accion, response=None, error=None, payment_id=None):
        if response is not None:
            self.sudo().create({
                'name': accion,
                'user': self.env.user.name,
                'url': response.url,
                'headers': response.headers,
                'payload': response.request.body,
                'response': response.text,
                'status': response.status_code,
                'error': str(error) if error else None,
                'payment': payment_id
            })

            # Guardamos los cambios en la base de datos
            self.env.cr.commit()
