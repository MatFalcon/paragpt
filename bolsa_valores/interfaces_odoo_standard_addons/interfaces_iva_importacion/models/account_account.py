from odoo import api, fields, models, exceptions


class AccountAccount(models.Model):
    _inherit = 'account.account'

    es_cuenta_iva_importacion = fields.Boolean('Es IVA Importación', default=False)
