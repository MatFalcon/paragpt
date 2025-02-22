# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bvpasa_reporte_facturas(models.Model):
#     _name = 'bvpasa_reporte_facturas.bvpasa_reporte_facturas'
#     _description = 'bvpasa_reporte_facturas.bvpasa_reporte_facturas'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
