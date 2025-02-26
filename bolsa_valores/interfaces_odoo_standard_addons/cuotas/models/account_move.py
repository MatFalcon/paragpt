from odoo import models,fields,api,exceptions

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    cuota_id=fields.Many2one('cuotas.cuota',string="Cuota",copy=False)