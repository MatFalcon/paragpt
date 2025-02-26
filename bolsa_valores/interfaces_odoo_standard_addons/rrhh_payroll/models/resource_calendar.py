from odoo import api, fields, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def _get_days_data(self, intervals, day_total):
        result = super(ResourceCalendar, self)._get_days_data(intervals, day_total)
        if result and 'days' in result and 'hours' in result:
            result['days'] = result.get('hours') / 8
        return result
