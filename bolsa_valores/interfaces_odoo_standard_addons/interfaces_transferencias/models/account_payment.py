from odoo import fields, api, models, exceptions


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    transferencia_id = fields.Many2one(
        'account.transferencia', string="Transferencia")
    journal_actual_id = fields.Many2one(
        'account.journal', string="Diario actual", default=lambda self: self.journal_id)

    parent_transfer_id=fields.Many2one('account.transferencia')

    motivo_transferencia=fields.Char(string="Motivo de la transferencia")
   
    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            if payment.payment_type == 'inbound' and not payment.journal_id.es_diario_tesoreria and not payment.is_internal_transfer:
                raise exceptions.ValidationError(
                    'No se puede recibir pagos en diarios que no sean de Tesoreria. Verifique la configuración de su diario')
            payment.write({'journal_actual_id': payment.journal_id.id})
        return res