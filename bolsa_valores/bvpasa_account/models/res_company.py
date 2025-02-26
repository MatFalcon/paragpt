# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError, UserError, RedirectWarning


class ResCompany(models.Model):
    _inherit = "res.company"

    def _validate_fiscalyear_lock(self, values):
        if values.get('fiscalyear_lock_date'):

            draft_entries = self.env['account.move'].search([
                ('company_id', 'in', self.ids),
                ('state', '=', 'draft'),
                ('date', '<=', values['fiscalyear_lock_date'])])
            #if draft_entries:
            #    for d in draft_entries:
            #        d.button_cancel()
            """error_msg = _('There are still unposted entries in the period you want to lock. You should either post or delete them.')
                action_error = {
                    'view_mode': 'tree',
                    'name': _('Unposted Entries'),
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', draft_entries.ids)],
                    'search_view_id': [self.env.ref('account.view_account_move_filter').id, 'search'],
                    'views': [[self.env.ref('account.view_move_tree').id, 'list'], [self.env.ref('account.view_move_form').id, 'form']],
                }
                raise RedirectWarning(error_msg, action_error, _('Show unposted entries'))"""

            unreconciled_statement_lines = self.env['account.bank.statement.line'].search([
                ('company_id', 'in', self.ids),
                ('is_reconciled', '=', False),
                ('date', '<=', values['fiscalyear_lock_date']),
                ('move_id.state', 'in', ('draft', 'posted')),
            ])
            """if unreconciled_statement_lines:
                error_msg = _("Todavía hay líneas de extractos bancarios sin conciliar en el período que deseas bloquear."
                            "Debes conciliarlas o eliminarlas.")
                action_error = {
                    'type': 'ir.actions.client',
                    'tag': 'bank_statement_reconciliation_view',
                    'context': {'statement_line_ids': unreconciled_statement_lines.ids, 'company_ids': self.ids},
                }
                raise RedirectWarning(error_msg, action_error, _('Mostrar línea de extracto bancario no conciliado'))"""
