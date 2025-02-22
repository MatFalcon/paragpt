from odoo import models

class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'
    
    def action_bank_automatic_reconcile(self):
        for line in self.line_ids.filtered(lambda x:not x.is_reconciled):
            statement_line = self.env['account.bank.statement.line'].browse(line.id)
            domain = []
            if line.partner_id:
                domain.append(('partner_id', '=', line.partner_id.id))

            query, params = self.env['account.reconciliation.widget']._get_query_reconciliation_widget_customer_vendor_matching_lines(statement_line,
                                                                                                 domain=domain)

            trailing_query, trailing_params = self.env['account.reconciliation.widget']._get_trailing_query(statement_line)

            self._cr.execute(query + trailing_query, params + trailing_params)
            results = self._cr.dictfetchall()
            move_lines = self.env['account.move.line'].browse(res['id'] for res in results)
            move_lines = move_lines.filtered(lambda x:x.account_id.user_type_id.type not in ['receivable','payable'])
            move_conciliar = move_lines.filtered(lambda x:x.move_id.payment_id.nro_documento == statement_line.payment_ref
                                                          or x.move_id.payment_id.nro_cheque == statement_line.payment_ref
                                                          or (x.date == statement_line.date and abs(x.balance) == abs(statement_line.amount)))
            vals = []
            if move_conciliar:
                for move_line in move_conciliar:
                    vals_list = {'partner_id': move_line.partner_id.id,
                             'lines_vals_list': [{'name': move_line.name,
                                                  'balance': move_line.debit * -1 if move_line.debit > 0 else move_line.credit,
                                                  'analytic_tag_ids': [[6, None, move_line.analytic_tag_ids]],
                                                  'id': move_line.id,
                                                  'currency_id': move_line.currency_id.id}],
                             'to_check': False}
                    vals.append(vals_list)
                self.env['account.reconciliation.widget'].process_bank_statement_line(line.id,vals)
            else:
                self.action_bank_reconcile_bank_statements()
