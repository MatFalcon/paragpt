# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class analytic_report(models.AbstractModel):
    _inherit = 'account.analytic.report'

    def _get_columns_name(self, options):
        return [{'name': ''},
                {'name': _('Referencia')},
                {'name': _('Empresa')},
                {'name': _('Balance'), 'class': 'number'},
                {'name': _('Balance (MS)'), 'class': 'number'}]

    def _generate_analytic_account_lines(self, analytic_accounts, parent_id=False):
        lines = []
        for account in analytic_accounts:
            lines.append({
                'id': 'analytic_account_%s' % account.id,
                'name': account.name,
                'columns': [{'name': account.code},
                            {'name': account.partner_id.display_name},
                            {'name': self.format_value(account.balance)},
                            {'name': self.format_value(account.balance_ms, account.secondary_currency_id)}],
                'level': 4,  # todo check redesign financial reports, should be level + 1 but doesn't look good
                'unfoldable': False,
                'caret_options': 'account.analytic.account',
                'parent_id': parent_id,  # to make these fold when the original parent gets folded
            })

        return lines