# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bvpasa_aprobacion_compras(models.Model):
#     _name = 'bvpasa_aprobacion_compras.bvpasa_aprobacion_compras'
#     _description = 'bvpasa_aprobacion_compras.bvpasa_aprobacion_compras'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
