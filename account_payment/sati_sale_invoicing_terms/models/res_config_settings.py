from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    contract_account_id = fields.Many2one(
        'account.account',
        string='Account for contracts',
        related='company_id.contract_account_id',
        readonly=False,
        help='This account will be used for contracts to be invoiced'
    )

    provition_account_id = fields.Many2one(
        'account.account',
        string='Account for provition of activated contracts',
        related='company_id.provition_account_id',
        readonly=False,
        help='This account will be used for activate provition of contracts'
    )

    provition_journal_id = fields.Many2one(
        'account.journal',
        related='company_id.provition_journal_id',
        string='Journal for provition account moves',
        readonly=False,
    )
