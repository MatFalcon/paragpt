from odoo import fields, api, models, exceptions


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    es_diario_tesoreria=fields.Boolean(string="Diario de tesoreria",help="Se debe elegir esta opción para los diarios de tipo Efectivo o Banco que sean internos de la empresa")