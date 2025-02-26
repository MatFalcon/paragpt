from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    diario_fg = fields.Boolean(string="Diario de Fondo de Garantia", default=False, copy=False)
