# -*- coding: utf-8 -*-
import psycopg2
import logging

from odoo import api, fields, models, tools,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # campo para numero de telefono personalizad por pdv
    pos_habilitar_nro_tel = fields.Boolean()
    pos_tel_punto_venta = fields.Char(related="pos_config_id.tel_punto_venta", readonly=False)
    pos_descripcion_compania = fields.Char(related="pos_config_id.descripcion_compania", readonly=False)
    pos_talonario_factura = fields.Many2one(
        related='pos_config_id.talonario_factura', readonly=False)
    pos_talonario_nota_credito = fields.Many2one(
        related='pos_config_id.talonario_nota_credito', readonly=False)
    pos_invoice_report = fields.Many2one(
        related='pos_config_id.talonario_nota_credito', readonly=False)
    ## agregar logica para el pie de pagina ##
    mensaje_factura = fields.Char(string="Mensaje que se muestra al final de ticket")


class PosConfigParaguay(models.Model):
    _inherit = "pos.config"
    habilitar_nro_tel = fields.Boolean()
    tel_punto_venta = fields.Char()
    descripcion_compania = fields.Char()

    invoice_report = fields.Many2one('ir.actions.report', string="Reporte de Factura",required=False,default=lambda self:self._get_company_invoice() )
    invoice_report_text = fields.Char(string='Reporte de Factura Char')
    talonario_factura = fields.Many2one('ruc.documentos.timbrados',string="Timbrado de Factura")
    talonario_nota_credito = fields.Many2one('ruc.documentos.timbrados',string="Timbrado de Nota de Credito")


    @api.constrains('invoice_report')
    def obtner(self):
        xml_id = None
        res = self.env['ir.model.data'].search([('model', '=', 'ir.actions.report'), ('res_id', '=', self.invoice_report.id)], limit=1)
        if res:
            id = self.invoice_report.id
            xml_id = res[id]
            if xml_id:
                self.invoice_report_text = xml_id


    @api.model
    def _get_company_invoice(self):
        repor= self.env.company.invoice_report
        informe= None
        if repor:
            informe= repor
        return informe
