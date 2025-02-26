from odoo import api, fields, models


class HREmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    banco_familiar_nro_cuenta = fields.Char(string='Nro Cuenta FAMILIAR')
