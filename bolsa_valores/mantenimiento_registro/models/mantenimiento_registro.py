# -*- coding: utf-8 -*-

from odoo import api, fields, models


class JornalMantenimiento(models.Model):
    _name = "mantenimiento_registro.jornal_mantenimiento"
    _description = "Jornales para el mantenimiento de registros"

    name = fields.Date(string="Fecha", required=True)
    monto = fields.Float(string="Monto", required=True)
    activo = fields.Boolean(string="Activo", default=False)

    # Al guardar un jornal se cambia el precio de los jornales de la lista de precios
    @api.model
    def create(self, vals):
        res = super(JornalMantenimiento, self).create(vals)

        # Si esta activo
        if res.activo:
            # Buscamos los jornales activos y desactivamos todos menos el que se esta creando
            jornales = self.env['mantenimiento_registro.jornal_mantenimiento'].search([('activo', '=', True)])
            if len(jornales) > 1:
                # Desactivamos todos menos el que se esta creando
                for jornal in jornales:
                    if jornal.id != res.id:
                        jornal.activo = False

            # Actualizamos las listas de precios
            lista_precios = self.env['mantenimiento_registro.lista_precios'].search([])
            if len(lista_precios) > 0:
                for jornal in lista_precios:
                    jornal.jornal = res.id
                    jornal._onchange_cantidad_jornales()

        return res

class ListaPrecios(models.Model):
    _name = "mantenimiento_registro.lista_precios"
    _description = "Lista de precios para el mantenimiento de registros"

    tipo_sociedad = fields.Selection(
        selection=[
            ('sae', 'SAE'),
            ('saeca', 'SAECA'),
            ('srl', 'SRL'),
            ('fideicomisos', 'Fideicomisos'),
            ('otros', 'Otros'),
        ],
        string='Tipo de sociedad'
    )

    name = fields.Char(string="Nombre", required=True)
    desde = fields.Float(string="Desde", required=True)
    hasta = fields.Float(string="Hasta", required=True)
    cantidad_jornales = fields.Integer(string="Cantidad de jornales", required=True)
    jornal = fields.Many2one('mantenimiento_registro.jornal_mantenimiento',
                             string="Jornal", domain=[('activo', '=', True)])
    monto = fields.Float(string="Total")

    # El monto se calcula multiplicando la cantidad de jornales por el monto del jornal
    @api.onchange('jornal', 'cantidad_jornales')
    @api.depends('jornal', 'cantidad_jornales')
    def _onchange_cantidad_jornales(self):
        for record in self:
            record.monto = record.cantidad_jornales * record.jornal.monto
