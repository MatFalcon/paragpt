from odoo import api, fields, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    allow_auto_checks = fields.Boolean(string='Permitir marcaciones automáticas', default=False)
