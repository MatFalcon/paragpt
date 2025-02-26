# -*- coding: utf-8 -*-

from odoo import models, fields, api, release


class ResCompany(models.Model):
    _inherit = 'res.company'

    if release.major_version in ['16.0']:
        reporte_libro_inventario_base_report_bg = fields.Many2one(
            'account.report',
            string='Reporte base para el Balance General',
        )

        reporte_libro_inventario_base_report_er = fields.Many2one(
            'account.report',
            string='Reporte base para el Estado de Resultados',
        )
    if release.major_version in ['15.0']:
        reporte_libro_inventario_base_report_bg = fields.Many2one(
            'account.financial.html.report',
            string='Reporte base para el Balance General',
        )

        reporte_libro_inventario_base_report_er = fields.Many2one(
            'account.financial.html.report',
            string='Reporte base para el Estado de Resultados',
        )
    show_libro_inventario_base_report_bg_details = fields.Boolean(
        string='Mostrar detalles de cuentas',
        default=True
    )
