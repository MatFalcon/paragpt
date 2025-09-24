# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class vencimiento_contrato(models.Model):
#     _name = 'vencimiento_contrato.vencimiento_contrato'
#     _description = 'vencimiento_contrato.vencimiento_contrato'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
