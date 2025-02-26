from odoo import fields, api, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    timbrados_ids = fields.One2many('interfaces_timbrado.timbrado', 'journal_id', string="Timbrados")
    max_lineas = fields.Integer(string="Cantidad máxima de líneas imprimibles de la factura", default=0)

    
    @api.onchange('timbrados_ids')
    @api.depends('timbrados_ids')
    def onchange_timbrados_ids(self):
        for r in self:
            r.timbrados_ids.journal_id = r.id