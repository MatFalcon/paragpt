from odoo import models, fields, api, exceptions


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    retencion_extranjeros = fields.Boolean(string="Retención Extranjeros", default=False, copy=False)