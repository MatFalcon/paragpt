# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bvpasa_presupuestos(models.Model):
#     _name = 'bvpasa_presupuestos.bvpasa_presupuestos'
#     _description = 'bvpasa_presupuestos.bvpasa_presupuestos'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
