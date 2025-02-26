from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    asiento_fg = fields.Boolean(string='Operaciones Diarias Fondo de Garantía')