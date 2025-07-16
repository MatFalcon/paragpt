# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api


class DiarioOrdenDePagos_(models.Model):
    _inherit = "account.journal"
    
    anticipo = fields.Boolean(string="Diario de anticipo?",help="Marcar en caso de que sea un diario para el manejo de anticipos de clientes y proveedores")
