from odoo import api, fields, models


class ResourceCalendarAttendance(models.Model):
    _inherit = 'resource.calendar.attendance'
    _order = 'dayofweek asc, hour_from asc'
