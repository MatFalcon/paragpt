from odoo import models,fields,api,exceptions


class AccountJournal(models.Model):
    _inherit = 'account.journal'


    remision_sequence_id=fields.Many2one('ir.sequence',string="Secuencia de notas de remisión")

