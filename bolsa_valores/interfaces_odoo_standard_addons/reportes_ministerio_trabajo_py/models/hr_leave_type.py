# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    ausencia_dias_corridos = fields.Boolean(string='Los días se cuentan de forma corrida')
    appears_in_mtess_reports = fields.Boolean('Aparece en los reportes para el MTESS', default=True)
    code = fields.Char(string='Código', required=True)
