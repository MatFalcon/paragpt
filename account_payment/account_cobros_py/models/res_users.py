
# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError



class UserRecibo(models.Model):
    _inherit = 'res.users'

    talonario_recibo_ids = fields.Many2many('account.recibo.talonario','usuario_talonario_recibo_id_rel','talonario_id','user_id',string='Talonario de recibo',ondelete='cascade')

