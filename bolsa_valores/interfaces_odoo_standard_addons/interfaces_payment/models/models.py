# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class interfaces_payment(models.Model):
#     _name = 'interfaces_payment.interfaces_payment'
#     _description = 'interfaces_payment.interfaces_payment'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
