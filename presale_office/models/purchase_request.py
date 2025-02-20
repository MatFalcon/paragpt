# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api , _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from lxml import etree
from datetime import datetime as dt
import logging


_logger = logging.getLogger(__name__)
class PurchaseRequest(models.Model):
    _inherit = ["purchase.request"]


    lead_id = fields.Many2one('crm.lead', string='Oportunidad Asociada', required=False)
    internal_purchase = fields.Boolean(string="Compra Interna")
    sale_order_id = fields.Many2one('sale.order',string="Venta de origen")

