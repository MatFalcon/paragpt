# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError


class diferencia_op(models.TransientModel):

    _name = 'diferencia.op'


    op_id = fields.Many2one('account.orden.pago',string="Orden de Pago")

    diferencia = fields.Selection([('a_cuenta','A Favor del Cliente/Anticipo')],string="Guardar Diferencia Como:",default='a_cuenta')








    def procesar(self):

        self.op_id.set_confirmado()

