# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class bvpasa_helpdesk(models.Model):
#     _name = 'bvpasa_helpdesk.bvpasa_helpdesk'
#     _description = 'bvpasa_helpdesk.bvpasa_helpdesk'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
