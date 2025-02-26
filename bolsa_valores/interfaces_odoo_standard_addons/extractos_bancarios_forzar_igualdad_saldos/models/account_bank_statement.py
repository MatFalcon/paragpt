from odoo import api, models, fields, exceptions


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    def button_post(self):
        for this in self:
            if this.balance_end_real != this.balance_end:
                raise exceptions.ValidationError('El Saldo Final no es igual al monto esperado (suma de todas las líneas del extracto)')
        return super(AccountBankStatement, self).button_post()
