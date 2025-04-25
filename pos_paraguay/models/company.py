# -*- coding: utf-8 -*-
import psycopg2
import logging

from odoo import api, fields, models, tools,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)


class FacturaParaguay(models.Model):
    _inherit = "res.company"
    
    invoice_report = fields.Many2one('ir.actions.report', string="Reporte de Factura")
    invoice_report_text = fields.Char(string='Reporte de Factura Char')

    # @api.constrains('invoice_report')
    # def obtner(self):
    #     xml_id = None
    #     res = self.invoice_report._for_xml_id()
    #     if res:
    #         id = self.invoice_report.id
    #         xml_id = res[id]
    #         if xml_id:
    #             self.invoice_report_text = xml_id

