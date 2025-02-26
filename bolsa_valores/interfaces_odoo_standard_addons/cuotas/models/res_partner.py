from odoo import models,api,fields,exceptions


class ResPartner(models.Model):
    _inherit = 'res.partner'


    cuotas_ids=fields.One2many('cuotas.cuota','partner_id',string="Cuotas")


