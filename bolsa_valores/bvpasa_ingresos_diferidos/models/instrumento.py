import datetime

from odoo import models, fields, api, exceptions

from odoo.addons.pbp.facturas.asientos import generar_asientos
from datetime import date, datetime, timedelta


class Instrumento(models.Model):
    _name = 'bvpasa_ingresos_diferidos.instrumento'
    _order = 'id desc'

    name = fields.Char(string='Nombre')
    active = fields.Boolean(string="Activo", default=True)
