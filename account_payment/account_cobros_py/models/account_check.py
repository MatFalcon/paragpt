# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api

class ReciboCheck(models.Model):
    _inherit = 'account.check.third'


    cuit = fields.Char(string="Nro. de Cuenta")

    @api.onchange('voucher_id')
    def _set_cuit(self):
        cuenta = self.env['res.partner.bank'].search([('partner_id','=',self.voucher_id.partner_id.id)],limit=1)
        if cuenta:
            self.cuit = cuenta.acc_number
            self.owner_name= cuenta.titular
            self.bank_id = cuenta.bank_id

