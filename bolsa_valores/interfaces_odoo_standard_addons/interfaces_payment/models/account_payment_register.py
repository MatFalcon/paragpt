from odoo import api, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    tipo_pago = fields.Selection(string='Tipo de pago', selection=[('Efectivo', 'Efectivo'), ('Cheque', 'Cheque'), (
        'TCredito', 'Tarjeta de crédito'), ('TDebito', 'Tarjeta de débito'),
                                                                   ('Transferencia', 'Transferencia / Depósito'),
                                                                   ('Retencion', 'Retención'), ('Otros', 'Otros')])
    nro_cheque = fields.Char(string='Nro. de cheque')
    bank_id = fields.Many2one('res.bank', string='Banco')
    fecha_cheque = fields.Date(string="Fecha del cheque")
    fecha_vencimiento_cheque = fields.Date(
        string="Fecha de vencimiento del cheque")
    nro_cuenta = fields.Char(string="Nro. de cuenta")
    nro_documento = fields.Char(string="Nro. de documento")
    observaciones = fields.Char(string="Observaciones")

    def _create_payment_vals_from_wizard(self):
        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': self.payment_type,
            'partner_type': self.partner_type,
            'ref': self.communication,
            'journal_id': self.journal_id.id,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_bank_id': self.partner_bank_id.id,
            #'payment_method_id': self.payment_method_id.id,
            'destination_account_id': self.line_ids[0].account_id.id,
            'tipo_pago':self.tipo_pago,
            'nro_cheque':self.nro_cheque,
            'bank_id': self.bank_id.id if self.bank_id else False,
            'fecha_cheque':self.fecha_cheque,
            'fecha_vencimiento_cheque':self.fecha_vencimiento_cheque,
            'nro_cuenta':self.nro_cuenta,
            'nro_documento':self.nro_documento,
            'observaciones':self.observaciones
        }

        if not self.currency_id.is_zero(self.payment_difference) and self.payment_difference_handling == 'reconcile':
            payment_vals['write_off_line_vals'] = {
                'name': self.writeoff_label,
                'amount': self.payment_difference,
                'account_id': self.writeoff_account_id.id,
            }
        return payment_vals
