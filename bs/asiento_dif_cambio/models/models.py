# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class asiento_dif_cambio(models.Model):
#     _name = 'asiento_dif_cambio.asiento_dif_cambio'
#     _description = 'asiento_dif_cambio.asiento_dif_cambio'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
