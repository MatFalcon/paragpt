import datetime

from odoo import models, fields, api, exceptions


class ResPartner(models.Model):
    _inherit = 'res.partner'

    con_contrato = fields.Boolean(string="Posee contrato")
    contratos_ids = fields.One2many('vencimiento_contrato.gestion_contrato', 'name', string="Contratos")
