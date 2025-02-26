# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class tipo_cambio_calculado(models.Model):
#     _name = 'tipo_cambio_calculado.tipo_cambio_calculado'
#     _description = 'tipo_cambio_calculado.tipo_cambio_calculado'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
