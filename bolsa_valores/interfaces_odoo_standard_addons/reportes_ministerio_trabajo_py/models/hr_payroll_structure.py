from odoo import fields, models, api


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    rule_ids = fields.One2many(copy=True)

    structure_type_tag = fields.Selection([
        ('normal', 'Normal'),
        ('vacacion', 'Vacación'),
        ('aguinaldo', 'Aguinaldo'),
    ], string='Etiqueta del Tipo de Estructura', related='type_id.structure_type_tag')
