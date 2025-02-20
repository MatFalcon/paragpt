# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError

class pos_session(models.Model):

    _inherit = "pos.session"

    # # @api.multi
    # def action_pos_session_closing_control(self):
    #     for rec in self:
    #         for statement in rec.statement_ids:
    #             for line in statement.line_ids:
