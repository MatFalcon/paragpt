# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from odoo.exceptions import ValidationError

class OrdenPagoWizard(models.TransientModel):
    _name='orden.pago.wizard'

    motivo_anulacion = fields.Many2one('ruc.motivo.anulacion',string="Motivo Anulacion", required=True)
    orden_pago_id=fields.Many2one('account.orden.pago', 'OrdenPago')

    def set_motivo_anulacion(self):
        for rec in self:
            if rec.orden_pago_id:
                # Verificar si orden_pago posee factura y/o cobros
                if not rec.orden_pago_id.payment_ids:
                    rec.orden_pago_id.motivo_anulacion=rec.motivo_anulacion
                    rec.orden_pago_id.state='anulado'
                else:
                    raise ValidationError('El orden_pago posee Facturas o Cobros relacionadas. Favor elimine las Facturas o Cobros para poder anular  ')
