# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        for rec in self:
            if any(factura.tipo_factura=='2' for factura in rec.line_ids.mapped('move_id')):
                if self.env.user.recibo_required:
                    raise ValidationError('Para registrar un cobro de facturas crédito, debe crear un recibo')
                else:
                    return super(AccountPaymentRegister, rec)._create_payments()
            else:
                return super(AccountPaymentRegister, rec)._create_payments()



