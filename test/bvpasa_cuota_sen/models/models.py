# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bvpasa_cuota_sen(models.Model):
#     _name = 'bvpasa_cuota_sen.bvpasa_cuota_sen'
#     _description = 'bvpasa_cuota_sen.bvpasa_cuota_sen'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
