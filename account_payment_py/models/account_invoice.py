# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    no_ver_factura_pago = fields.Boolean(default=False, store=True)
    monto_a_pagar = fields.Float(string="Monto a pagar")

class AccountInvoice(models.Model):
    _inherit = 'account.move.line'

    no_ver_factura_pago = fields.Boolean(default=False, store=True)
    monto_a_pagar = fields.Float(string="Monto a pagar")

