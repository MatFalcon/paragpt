from odoo import _, api, fields, models,exceptions




class AccountMove(models.Model):
    _inherit = 'account.move'


    nota_remision_id=fields.Many2one('notas_remision_account.nota.remision','Nota de remisión',copy=False,tracking=True)