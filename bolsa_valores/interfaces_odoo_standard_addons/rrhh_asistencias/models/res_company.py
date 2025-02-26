# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    overtime_employee_threshold_early_leaves = fields.Integer(
        string='Tiempo de tolerancia para salidas anticipadas',
    )

    @api.model
    def _check_extra_hours_time_off(self):
        return
