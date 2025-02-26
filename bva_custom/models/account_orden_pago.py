# -*- coding: UTF-8 -*-

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError

class OrdenPago(models.Model):
    _inherit = 'account.orden.pago'

    def set_pendiente(self):
        self.state = 'pendiente'