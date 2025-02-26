from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'

    novedades_sen_ids = fields.One2many(
        'pbp.novedades_sen',  # Related model
        'invoice_id',         # Field in pbp.novedades_sen that links to account.move
        string='Novedades SEN'
    )
    cartera_id = fields.Many2one(
        'pbp.cartera_inversion',
        string="Cartera de Inversión",
        ondelete='cascade'
    )
    initial_cartera_id = fields.Many2one(
        'pbp.cartera_inversion',
        string="Cartera de Inversión (Inicial)",
        ondelete='cascade'
    )
