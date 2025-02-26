# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class AntiguedadVacaciones(models.Model):
    _name = 'antiguedad.vacaciones'
    _description = 'Dias de vacaciones según antiguedad en días'

    antiguedad_dias = fields.Integer(string='Días de antiguedad')
    dias_vacaciones = fields.Integer(string='Días de vacaciones correspondientes')
