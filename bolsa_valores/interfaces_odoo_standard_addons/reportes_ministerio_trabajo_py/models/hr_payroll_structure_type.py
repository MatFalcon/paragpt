from odoo import fields, models, api


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    wage_type = fields.Selection(selection_add=[('daily', 'Salario por Día')], default='monthly', ondelete={
        'daily': 'set default'
    })
    structure_type_tag = fields.Selection([
        ('normal', 'Normal'),
        ('vacacion', 'Vacación'),
        ('aguinaldo', 'Aguinaldo'),
    ], string='Etiqueta del Tipo de Estructura', default='normal', required=True)
