
# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError



class UserRecibo(models.Model):
    _inherit = 'res.users'

    recibo_required = fields.Boolean(string="Recibo obligatorio en facturas cred.")

