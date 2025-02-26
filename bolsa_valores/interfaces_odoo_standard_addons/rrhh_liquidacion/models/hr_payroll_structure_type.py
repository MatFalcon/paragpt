from odoo import fields, models, api


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

    structure_type_tag = fields.Selection(selection_add=[
        ('liquidacion', 'Liquidación'),
    ], ondelete={'liquidacion': 'set default'})
