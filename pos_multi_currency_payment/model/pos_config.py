# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class pos_config(models.Model):

    _inherit = "pos.config"

    multi_currency = fields.Boolean('Multi currency', default=1)
    multi_currency_update_rate = fields.Boolean('Update rate', default=1)
