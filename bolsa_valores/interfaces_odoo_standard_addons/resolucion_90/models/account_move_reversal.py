from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):
        result = super(AccountMoveReversal, self).reverse_moves()
        account_move = self.env[result.get('res_model')].browse(result.get('res_id'))
        name = ', '.join(self.move_ids.mapped('name'))
        if self.move_type in ['in_invoice']:
            if self.move_ids.mapped('ref'):
                name = ', '.join(self.move_ids.mapped('ref'))
            else:
                name = ''
        account_move.update({
            'res90_nro_comprobante_asociado': name,
            'res90_timbrado_comprobante_asociado': ', '.join(move.res90_nro_timbrado or "" for move in self.move_ids),
        })
        return result
