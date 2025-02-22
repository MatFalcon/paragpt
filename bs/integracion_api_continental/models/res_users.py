# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = "res.users"

    api_continental_carga = fields.Boolean(string="Puede realizar cargas")
    api_continental_autoriza = fields.Boolean(string="Puede autorizar")
