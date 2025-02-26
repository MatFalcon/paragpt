from odoo import models, fields, api, exceptions


class ResCompany(models.Model):
    _inherit = 'res.company'

    res90_imputa_irp_rsp_defecto = fields.Boolean(string="Imputa IRP/RSP por defecto")