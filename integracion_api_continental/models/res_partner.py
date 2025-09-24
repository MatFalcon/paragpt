# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    tipo_documento = fields.Selection(
        selection=[
            ("RUC", "RUC"),
            ("CI", "CEDULA DE IDENTIDAD PARAGUAYA"),
            ("PAS", "PASAPORTE"),
            ("REG", "REGISTRO DE CONDUCIR"),
            ("JUB", "PADRON CAJA JUBILACIONES"),
            ("IPS", "NRO.ASEGURADO IPS"),
            ("CRP", "CRP"),
            ("CRC", "CRC - DOCUMENTO EXTRANJERO"),
            ("CIV", "LIBRETA CIVICA"),
            ("BAJ", "LIBRETA DE BAJA"),
            ("ANT", "CERTIFICADO ANTECEDENTES"),
        ],
        string="Tipo de Documento",
    )
