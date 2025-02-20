# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)

class account_journal(models.Model):
    _inherit = "account.journal"

    pos_currency_id = fields.Many2one('res.currency',string="Moneda POS")