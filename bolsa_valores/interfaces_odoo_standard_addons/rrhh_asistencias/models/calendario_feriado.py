# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _
from datetime import timedelta


class CalendarioFeriado(models.Model):
    _inherit = 'calendario.feriado'
    _description = 'Lista de feriados'

    custom_factor = fields.Boolean(string='Factores personalizados para cálculo de horas', default=False)
    factor_horas_extra_100 = fields.Float(string='Factor para Horas extra 100%', default=1)
    factor_horas_nocturnas = fields.Float(string='Factor para Horas Nocturnas', default=1)
