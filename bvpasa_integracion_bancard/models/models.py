# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bvpasa_integracion_bancard(models.Model):
#     _name = 'bvpasa_integracion_bancard.bvpasa_integracion_bancard'
#     _description = 'bvpasa_integracion_bancard.bvpasa_integracion_bancard'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
