# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class tipo_obligaciones(models.Model):
    _name = 'tipo.obligaciones'


    name = fields.Char(string='Nombre de Obligacion',tracking=True)
    code = fields.Integer(string="Codigo",tracking=True)
    active = fields.Boolean(string="Activo",default=True,tracking=True)