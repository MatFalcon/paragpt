# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class derivacion_tickets(models.Model):
#     _name = 'derivacion_tickets.derivacion_tickets'
#     _description = 'derivacion_tickets.derivacion_tickets'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
