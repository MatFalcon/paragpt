# -*- coding: utf-8 -*-

from odoo import exceptions, fields, models


class AccountJournal(models.Model):
    _inherit = "account.journal"

    api_continental_hash = fields.Char(string="HASH de la cuenta")
    is_continental = fields.Boolean(string="Es una cuenta de Continental")
