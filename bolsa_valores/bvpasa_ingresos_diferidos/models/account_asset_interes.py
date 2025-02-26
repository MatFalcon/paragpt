import datetime

from odoo import models, fields, api, exceptions

from odoo.addons.pbp.facturas.asientos import generar_asientos
from datetime import date, datetime, timedelta


class AccounAssetIntereses(models.Model):
    _name = 'bvpasa_ingresos_diferidos.interes'
    _order = 'state, fecha_compra desc'
    _rec_name = 'id'

    emisor_id = fields.Many2one('res.partner', string="Emisor")
    tipo = fields.Selection(selection=[
            ('intereses', 'Intereses'),
            ('capital', 'Capital'),
        ], default="", string="Tipo")
    estado = fields.Selection(selection=[
            ('vencido', 'Vencido'),
            ('cobrado', 'Cobrado'),
            ('activo', 'Activo'),
        ], default="", string="Estado")
    grupo_id = fields.Many2one('bvpasa_ingresos_diferidos.interes_grupo',string="Grupo")
    casa_bolsa_id = fields.Many2one('res.partner', string="Casa de Bolsa")
    serie_id = fields.Many2one('emisiones.series', string="Serie")
    fecha_compra = fields.Date(string="Fecha de Compra")
    fecha_vencimiento_serie = fields.Date(string="Fecha de Vencimiento Serie")
    calificacion_riesgo_id = fields.Many2one('bvpasa_ingresos_diferidos.calificacion_riesgo', string="Calificación de Riesgo")
    instrumento_id = fields.Many2one('bvpasa_ingresos_diferidos.instrumento',string="Instrumento")
    tasa_interna = fields.Float(string="Tasa Interna")
    currency_id = fields.Many2one('res.currency',string="Moneda")
    importe_valorizado = fields.Monetary(string="Importe Valorizado")

