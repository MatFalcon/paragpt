# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import fields, models
    
class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_a_doctor = fields.Boolean(string="Is a Doctor")

    numero_matricula = fields.Char(string='N° Matrícula')