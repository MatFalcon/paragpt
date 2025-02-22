from odoo import models, fields, api, exceptions,_
from odoo.exceptions import UserError
from odoo.osv import expression

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.model
    def _domain_move_lines_for_manual_reconciliation(self, account_id, partner_id=False, excluded_ids=None,search_str=''):
        """ Create domain criteria that are relevant to manual reconciliation. """
        domain = ['&', '&', ('reconciled', '=', False), ('account_id', '=', account_id),
                  ('move_id.state', '=', 'posted')]
        if partner_id:
            domain = expression.AND([domain, [('partner_id', '=', partner_id)]])
        if excluded_ids:
            domain = expression.AND([[('id', 'not in', excluded_ids)], domain])
        if search_str:
            str_domain = self._get_search_domain(search_str=search_str)
            domain = expression.AND([domain, str_domain])
        # filter on account.move.line having the same company as the given account
        account = self.env['account.account'].browse(account_id)
        domain = expression.AND([domain, [('company_id', '=', account.company_id.id)]])
        return domain
