# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HREmployee(models.Model):
    _inherit = 'hr.employee'

    # cuenta_bancaria = fields.Char(string='Cuenta Bancaria')
