# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api


class ResCountry(models.Model):
    _inherit = 'res.country'

    demonym = fields.Char(compute='_get_demonym')

    def _get_demonym(self):
        paises = {
            'PY': 'Paraguaya',
            'BO': 'Boliviana',
            'US': 'Norteamericana',
            'DE': 'Alemana',
            'BR': 'Brasilera',
            'CA': 'Canadiense',
        }
        for this in self:
            this.demonym = paises.get(this.code) if paises.get(this.code) else this.name
