# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class AccountCheck(models.Model):
    _inherit = 'account.check'

    orden_pago_id = fields.Many2one('account.orden.pago')