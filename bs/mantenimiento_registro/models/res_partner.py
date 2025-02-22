# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    tipo_sociedad = fields.Selection(
        selection=[
            ('sae', 'SAE'),
            ('saeca', 'SAECA'),
            ('srl', 'SRL'),
            ('fideicomisos', 'Fideicomisos'),
            ('otros', 'Otros'),
        ],
        string='Tipo de sociedad'
    )

    capital = fields.Float(string='Capital')
