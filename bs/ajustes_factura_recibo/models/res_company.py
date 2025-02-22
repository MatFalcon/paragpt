# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompanyBvpasa(models.Model):
    _inherit = 'res.company'
    _description = 'ajustes_factura_recibo.res_company_bvpasa'

    rubro_set = fields.Char('Rubro')

    