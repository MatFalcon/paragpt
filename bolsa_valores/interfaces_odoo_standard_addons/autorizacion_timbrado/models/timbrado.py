from odoo import fields, api, models, exceptions


class Timbrado(models.Model):
    _inherit = 'interfaces_timbrado.timbrado'

    nro_autorizacion = fields.Char('Número Autorización')