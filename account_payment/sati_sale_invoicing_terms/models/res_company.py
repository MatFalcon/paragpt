from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    contract_account_id = fields.Many2one(
        'account.account',
        string='Account for contracts',
        help='This account will be used for contracts to be invoiced'
    )

    provition_account_id = fields.Many2one(
        'account.account',
        string='Account for provition of activated contracts',
        help='This account will be used for activate provition of contracts'
    )

    provition_journal_id = fields.Many2one(
        'account.journal',
        string='Journal for provition account moves',
        readonly=False,
    )
