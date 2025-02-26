from odoo import models, fields

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    novedades_sen_ids = fields.One2many(
        'pbp.novedades_sen',  # Related model
        'invoice_id',         # Field in pbp.novedades_sen that links to account.move
        string='Novedades SEN'
    )
    carteras_ids = fields.One2many(
        'pbp.cartera_inversion',
        'voucher_id',
        string="Carteras de Inversión"
    )
    vencimiento_id = fields.Many2one("pbp.vencimiento_capital_interes",
                                     string="Vencimiento")
