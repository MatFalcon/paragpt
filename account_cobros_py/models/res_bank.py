
# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError



class ResBank(models.Model):
    _inherit = 'res.partner.bank'

    titular = fields.Char(string="Titular")


