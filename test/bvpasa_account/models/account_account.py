import datetime

from odoo import models, fields, api, exceptions


class AccountAccount(models.Model):
    _inherit = 'account.account'

    tag_ids = fields.Many2many('account.account.tag', 'account_account_account_tag', string='Etiquetas',
                               help="Etiquetas a asignar en informes personalizados.", required=True)
