# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class autorizacion_timbrado(models.Model):
#     _name = 'autorizacion_timbrado.autorizacion_timbrado'
#     _description = 'autorizacion_timbrado.autorizacion_timbrado'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
