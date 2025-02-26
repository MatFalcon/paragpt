from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payroll_structure_default_despido = fields.Many2one(
        'hr.payroll.structure',
        string='Estructura para Despidos',
        related='company_id.payroll_structure_default_despido',
        help='Estructura que se utilizará por defecto para las nóminas de Despidos',
        readonly=False
    )
    payroll_structure_default_renuncia = fields.Many2one(
        'hr.payroll.structure',
        string='Estructura para Renuncias',
        related='company_id.payroll_structure_default_renuncia',
        help='Estructura que se utilizará por defecto para las nóminas de Renuncias',
        readonly=False
    )
