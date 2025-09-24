from odoo import models, fields


class AccountCustom(models.Model):
    _inherit = 'account.account'

    cartera_acreedor_deudor = fields.Selection(
        selection=[
            ('acreedor', 'Acreedor'),
            ('deudor', 'Deudor'),
        ],
        string='Tipo de cuenta',
    )

    cartera_tipo = fields.Selection(
        selection=[
            ('intereses', 'Intereses'),
            ('capital', 'Capital'),
        ],
        string='Tipo de cartera',
    )

    cartera_currency_id = fields.Many2one('res.currency', string='Moneda')

    cartera_vencimiento = fields.Selection(
        selection=[
            ('corto_plazo', 'Corto Plazo'),
            ('largo_plazo', 'Largo Plazo'),
        ],
        string='Vencimiento',
    )

    cartera_instrumento = fields.Selection(
        selection=[
            ('acciones', 'Acciones'),
            ('bonos', 'Bonos'),
            ('bonos_cartulares', 'Bonos Cartulares'),
            ('bonos_corporativos', 'Bonos Corporativos'),
            ('bonos_del_tesoro', 'Bonos del Tesoro'),
            ('bonos_financieros', 'Bonos Financieros'),
            ('bonos_subordinados', 'Bonos Subordinados'),
            ('cda', 'CDA'),
            ('fondos', 'Fondos'),
        ],
        string='Instrumento',
    )
