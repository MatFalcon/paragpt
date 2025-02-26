# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResCompany(models.Model):
    _inherit = "res.company"

    api_continental_pp_user_carga = fields.Char(string="Usuario carga")
    api_continental_pp_pass_carga = fields.Char(string="Contraseña carga")
    api_continental_pp_user_autoriza = fields.Char(string="Usuario autoriza")
    api_continental_pp_pass_autoriza = fields.Char(string="Contraseña autoriza")

    api_continental_sc_user_carga = fields.Char(string="Usuario carga")
    api_continental_sc_pass_carga = fields.Char(string="Contraseña carga")
    api_continental_sc_user_autoriza = fields.Char(string="Usuario autoriza")
    api_continental_sc_pass_autoriza = fields.Char(string="Contraseña autoriza")

    api_continental_ps_user_carga = fields.Char(string="Usuario carga")
    api_continental_ps_pass_carga = fields.Char(string="Contraseña carga")
    api_continental_ps_user_autoriza = fields.Char(string="Usuario autoriza")
    api_continental_ps_pass_autoriza = fields.Char(string="Contraseña autoriza")

    api_continental_subscription_pp = fields.Char(string="Pago de Proveedores")
    api_continental_subscription_ps = fields.Char(string="Pago de Salario")
    api_continental_subscription_sc = fields.Char(string="Servicios Corporativos")
    api_continental_subscription_ce = fields.Char(string="Cuentas y Extractos")

    # Agregamos un campo del tipo file, para cargar un archivo .pfx
    api_continental_cert_path = fields.Binary(string="Certificado")
    api_continental_cert_pass = fields.Char(string="Contraseña del certificado", help="Contraseña del certificado .pfx")

    # Datos de autorizacion
    api_continental_codigo_cliente = fields.Char(string="Codigo de Cliente")
    api_continental_ruc = fields.Char(string="RUC (sin guión)")
    api_continental_url = fields.Char(string="URL")
