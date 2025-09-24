import datetime

from odoo import models, fields, api, exceptions


class ResPartner(models.Model):
    _inherit = 'res.partner'

    factura_cuota_sen_id = fields.Many2one('account.move', string="Factura Cuota S.E.N.", copy=False)

    cuota_sen_ids = fields.One2many('bvpasa_cuota_sen.facturas_cuota_sen','partner_id', string="Cuotas S.E.N.")