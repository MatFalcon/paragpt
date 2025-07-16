# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from odoo.exceptions import ValidationError

class ReciboWizard(models.TransientModel):
    _name='recibo.wizard'

    motivo_anulacion = fields.Many2one('ruc.motivo.anulacion',string="Motivo Anulacion", required=True)
    recibo_id=fields.Many2one('account.recibo', 'Recibo')

    def set_motivo_anulacion(self):
        for rec in self:
            if rec.recibo_id:
                # Verificar si recibo posee factura y/o cobros
                if not rec.recibo_id.payment_ids and not rec.recibo_id.invoice_ids:
                    rec.recibo_id.motivo_anulacion=rec.motivo_anulacion
                    rec.recibo_id.state='anulado'
                    rec.recibo_id.dias_en_borrador = 0
                else:
                    raise ValidationError('El recibo posee Facturas o Cobros relacionadas. Favor elimine las Facturas o Cobros para poder anular  ')
