# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api

class DiarioRecibo(models.Model):
    _inherit = "account.journal"

    recibo_diario = fields.Boolean(string='Diario para Recibo', default=False, store=True)
    tipo_reporte=fields.Selection([('efectivo','Efectivo'),('cheques','Cheques'),
                                   ('tarjeta_credito','Tarjeta de Credito'),
                                   ('tarjeta_debito','Tarjeta de debito'),
                                   ('retencion','Retencion'),('transferencia','Transferencia')],default="efectivo")


