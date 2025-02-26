# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.http import request
import base64, datetime, calendar


class ReporteSET(models.TransientModel):
    _name = 'reporte_set'
    _description = 'Wizard para el reporte de la SET'

    company_ids = fields.Many2many('res.company', string="Compañias", required=True, default=lambda self: self.env.companies)
    year = fields.Integer(string='Año', required=True, default=lambda self: fields.Date.today().year - 1)

    def download_reports(self, **kw):
        dt = str(datetime.datetime.today())
        if request.env.user.has_group('hr.group_hr_manager'):
            return {
                'type': 'ir.actions.act_url',
                'url': '/reportes_ministerio_trabajo/reporte_set_zip?cids=' + str(
                    ','.join([str(company.id) for company in self.company_ids])) + '&year=' + str(
                    self.year) + '&dt=' + str(dt),
                'target': 'self',
            }
        else:
            return werkzeug.utils.redirect('/web/login')
