# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def create(self, vals):
        if vals.get('city_id'):
            ciudad = self.env['res.city'].search([('id','=',vals.get('city_id'))])
            vals.update({'city':ciudad.name})
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        if vals.get('city_id'):
            ciudad = self.env['res.city'].search([('id','=',vals.get('city_id'))])
            vals.update({'city': ciudad.name})
        return super(ResPartner, self).write(vals)


