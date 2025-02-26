from odoo import _, api, fields, models



class StockPicking(models.Model):
    _inherit = 'stock.picking'


    nota_remision_id=fields.Many2one('notas_remision_account.nota.remision',string='Nota de remisión',copy=False,tracking=True)