from odoo import api, fields, models


class res_partner(models.Model):
    _inherit = 'res.partner'

    timbrado_id = fields.One2many(comodel_name='proveedores_timbrado.timbrado', inverse_name='partner_id', string='Timbrado')
    