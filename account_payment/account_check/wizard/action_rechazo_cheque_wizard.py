from odoo import models, fields, api , _
from odoo.exceptions import ValidationError

class ActionRechazoChequeWizard(models.TransientModel):
    _name = 'action.rechazo.cheque.wizard'
    _description = 'Action rechazo cheque wizard'

    check_id = fields.Many2one('account.check.third', string="Cheque")
    date = fields.Date(string="Fecha de rechazo")
    journal_id = fields.Many2one('account.journal',string="Diario"
                                                          "")
    account_id = fields.Many2one('account.account', string='Cuenta contable de rechazo')

    def action_rechazar(self):
        fecha = self.date
        if self.check_id.deposit_account_move_id:
            credito = []
            debito = []
            journal = self.journal_id
            if self.check_id.currency_id != self.env.company.currency_id:
                moneda_ex = 1
            else:
                moneda_ex = 0
            monto_total = 0
            ref = 'Rechazo de Cheque Nro: ' + str(self.check_id.number)

            move_vals = {
                'journal_id': journal.id,
                'date': fecha,
                'ref': ref,
            }
            move = self.env['account.move'].with_context({}).create(move_vals)
            if moneda_ex == 1:
                monto_ex = self.check_id.currency_id.with_context(name=self.check_id.deposit_account_move_id.date).compute(self.check_id.amount,
                                                                                                         self.env.company.currency_id)
                monto_moneda = self.check_id.amount


            else:
                monto_ex = self.check_id.amount
                monto_moneda = 0

            monto_total += monto_ex
            debi = {
                'name': ref,
                'account_id': self.account_id.id,
                'move_id': move.id,
                'debit': monto_ex,
                'currency_id': self.check_id.currency_id.id,
                'amount_currency': monto_moneda,
                'credit': 0,
                'ref': ref,
            }
            debito.append(debi)
            move.line_ids.with_context({}).create(debi)
            for lineas in self.check_id.deposit_account_move_id.line_ids:
                if lineas.debit > 0:
                    cuenta_destino = lineas.account_id
            credi = {
                'name': ref,
                'account_id': cuenta_destino.id,
                'move_id': move.id,
                'debit': 0,
                'currency_id': self.check_id.currency_id.id,
                'amount_currency': monto_moneda,
                'credit': monto_ex,
                'ref': ref,
            }
            credito.append(credi)
            move.line_ids.with_context({}).create(credi)
            move.action_post()
            self.check_id.asiento_rechazo = move
            self.check_id.state = 'rechazado'
            self.check_id.cuenta_origen = self.account_id.id
        return {'type': 'ir.actions.act_window_close'}
