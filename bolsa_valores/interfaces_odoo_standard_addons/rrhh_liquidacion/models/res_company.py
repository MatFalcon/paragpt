# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'res.company'

    payroll_structure_default_despido = fields.Many2one(
        'hr.payroll.structure',
        string='Estructura para Despidos',
    )
    payroll_structure_default_renuncia = fields.Many2one(
        'hr.payroll.structure',
        string='Estructura para Renuncias',
    )
