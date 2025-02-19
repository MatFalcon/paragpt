# -*- coding: utf-8 -*-
from odoo import models, fields, api
from num2words import num2words
import logging
import random
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class TimbradoFactElect(models.Model):
    _inherit = 'ruc.documentos.timbrados'

    timbrado_electronico = fields.Selection(selection=[
        ('1', 'Factura electrónica'),
        ('2', 'Factura electrónica de exportación'),
        ('3', 'Factura electrónica de importación'),
        ('4', 'Autofactura electrónica'),
        ('5', 'Nota de crédito electrónica'),
        ('6', 'Nota de débito electrónica'),
        ('7', 'Nota de remisión electrónica'),
        ('8', 'Comprobante de retención electrónico')
    ], string="Tipo Documento Electrónico")

    actividad_economica_ids = fields.One2many(
        'res.company.actividad',
        'timbrado_id',
        string="Actividades Económicas"
    )

    serie = fields.Char(string="Serie", size=2)

    es_facturador_electronico = fields.Boolean(
        string="Es Facturador Electrónico",
        compute="_compute_es_facturador_electronico"
    )

    @api.depends('company_id')
    def _compute_es_facturador_electronico(self):
        for rec in self:
            rec.es_facturador_electronico = bool(rec.company_id and rec.company_id.servidor)

    @api.constrains('actividad_economica_ids')
    def _check_actividad_economica_limit(self):
        for record in self:
            if len(record.actividad_economica_ids) > 9:
                raise ValidationError("No puedes agregar más de 9 actividades económicas.")


class CompanyActividadEconomica(models.Model):
    _name = 'res.company.actividad'
    _description = 'Actividades Económicas de la Empresa'

    timbrado_id = fields.Many2one(
        'ruc.documentos.timbrados',
        string="Timbrado",
        ondelete='cascade'
    )

    codigo_actividad = fields.Char(
        string="Código de Actividad Económica",
        required=True,
        help="Código de actividad económica según la SET. En caso de solo utilizar una actividad económica se puede dejar vacío y cargar el dato en la compañía."
    )
    actividad_economica = fields.Char(string="Actividad Económica", required=True)

    tipo_actividad = fields.Selection([
        ('principal', 'Principal'),
        ('secundaria', 'Secundaria')
    ], string="Tipo de Actividad", required=True)


