# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError


class wizard_asignacion(models.TransientModel):

    _name = 'account_payment_py.wizard_asignacion'


    op_id = fields.Many2one('account.orden.pago',string="Orden de Pago")

    invoice_ids = fields.Many2many('account.move',string="Facturas")
    partner_id = fields.Many2one('res.partner')
    currency_id = fields.Many2one('res.currency')


    def limpiar(self):
        self.ensure_one()
        self.invoice_ids = None
        return {
            "type": "set_scrollTop",
        }

    def procesar(self):
        self.ensure_one()
        if len(self.invoice_ids) > 0:
            for inv in self.invoice_ids:
                inv.no_ver_factura_pago=True
                values= {'invoice_id':inv.id,'monto':inv.amount_residual}
                self.op_id.orden_pagos_facturas_ids = [((0, 0, values))]
                try:
                    self.op_id._actualizar_monto_retencion()
                except:
                    continue


