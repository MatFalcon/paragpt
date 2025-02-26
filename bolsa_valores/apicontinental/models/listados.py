# -*- coding: utf-8 -*-
from odoo import api, fields, models


class BancosDestino(models.Model):
    _name = "apicontinental.listado_banco_destino"
    _description = "Lista de bancos de destino"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", required=True)


class TiposDocumentos(models.Model):
    _name = "apicontinental.listado_tipo_documento"
    _description = "Lista de tipos de documentos"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", required=True)


class MotivosTransaccion(models.Model):
    _name = "apicontinental.listado_motivo_transaccion"
    _description = "Lista de motivos de transaccion"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", required=True)


class ProcedenciaFondos(models.Model):
    _name = "apicontinental.listado_procedencia_fondo"
    _description = "Lista de procedencia de fondos"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", required=True)


class Monedas(models.Model):
    _name = "apicontinental.listado_moneda"
    _description = "Lista de monedas"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", required=True)


class Sucursales(models.Model):
    _name = "apicontinental.listado_sucursal"
    _description = "Lista de sucursales"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", required=True)


class Sexo(models.Model):
    _name = "apicontinental.listado_sexo"
    _description = "Lista de sexo"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", required=True)


class TipoIngreso(models.Model):
    _name = "apicontinental.listado_tipo_ingreso"
    _description = "Lista de tipo de ingreso"

    name = fields.Char(string="Nombre", required=True)
    code = fields.Char(string="Codigo", required=True)
