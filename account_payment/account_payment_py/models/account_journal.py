# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api


class DiarioOrdenDePagos_(models.Model):
    _inherit = "account.journal"
    
    retencion = fields.Boolean(string="Diario Para retencion")
    orden_pago_diario = fields.Boolean(string='Diario para Orden de Pago', default=False, store=True)