# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ArancelesCantidad(models.Model):
    _name = 'custodia_fisica.aranceles_cantidad'
    _description = 'custodia_fisica.aranceles_cantidad'

    name = fields.Char(string="Nombre")
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    predeter = fields.Boolean(string="Arancel Predeterminado", default=False)
    line_ids = fields.One2many(
        'custodia_fisica.aranceles_cantidad_line', 'arancel_cantidad_id')
    activo = fields.Boolean(string="Activo", default=True)


class ArancelesCantidadLine(models.Model):
    _name = 'custodia_fisica.aranceles_cantidad_line'
    _description = 'custodia_fisica.aranceles_cantidad_line'

    arancel_cantidad_id = fields.Many2one('custodia_fisica.aranceles_cantidad')
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    cantidad_desde = fields.Float(string="Cantidad desde")
    cantidad_hasta = fields.Float(string="Cantidad hasta")
    jornales = fields.Float(string="Jornales")


class ArancelesMonto(models.Model):
    _name = 'custodia_fisica.aranceles_monto'
    _description = 'custodia_fisica.aranceles_monto'

    name = fields.Char(string="Nombre")
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string="Moneda")
    predeter = fields.Boolean(string="Arancel Predeterminado", default=False)
    line_ids = fields.One2many(
        'custodia_fisica.aranceles_monto_line', 'arancel_monto_id')
    activo = fields.Boolean(string="Activo", default=True)


class ArancelesMontoLine(models.Model):
    _name = 'custodia_fisica.aranceles_monto_line'
    _description = 'custodia_fisica.aranceles_monto_line'

    arancel_monto_id = fields.Many2one('custodia_fisica.aranceles_monto')
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    monto_desde = fields.Float(string="Monto desde")
    monto_hasta = fields.Float(string="Monto hasta")
    jornales = fields.Float(string="Jornales")
