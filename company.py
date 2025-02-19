# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)

class CompanyFactElect(models.Model):
    _inherit = 'res.company'

    regimen=fields.Selection(selection=[('1' , 'Régimen de Turismo'),
                              ('2' , 'Importador'),
                                ('3' , 'Exportador'),
                                ('4' , 'Maquila'),
                                ('5' , 'Ley N° 60/90'),
                                ('6' , 'Régimen del Pequeño Productor'),
                                ('7' , 'Régimen del Mediano Productor'),
                                ('8' , 'Régimen Contable')
                                ])
    nro_casa=fields.Char()
    actividad_economica=fields.Char()
    codigo_actividad=fields.Char()
    servidor=fields.Selection(selection=[('produccion','Produccion'),('prueba','Prueba')])
    IdCSC=fields.Char()
    csc=fields.Char(string='CSC')
    tipo_transaccion = fields.Selection(selection=[('1', 'Venta de mercadería'),
                                                   ('2', 'Prestación de servicios'),
                                                   ('3', 'Mixto'),
                                                   ('4', 'Venta de activo fijo'),
                                                   ('5', 'Venta de divisas'),
                                                   ('6', 'Compra de divisas'),
                                                   ('7', 'Promoción o entrega de muestras'),
                                                   ('8', 'Donación'),
                                                   ('9', 'Anticipo'),
                                                   ('10', 'Compra de productos'),
                                                   ('11', 'Compra de servicios'),
                                                   ('12', 'Venta de crédito fiscal'),
                                                   ('13', 'Muestras médicas')
                                                   ], default='2', string='Tipo de Transaccion por defecto')


    # @api.onchange('servidor')
    # def controlar_servidor(self):
    #     if self.servidor:
    #         if self.servidor == 'produccion':
    #             raise ValidationError('La utilizacion del servidor de produccion  no esta aun habilitado')
