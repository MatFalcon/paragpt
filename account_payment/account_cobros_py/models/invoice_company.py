from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from num2words import num2words

class company(models.Model):
    _inherit = "res.company"
    # acti1=fields.Char(string="Actividad Comercial")
    # acti2=fields.Char(string="Actividad Comercial")
    # actividad3=fields.Char(string="Actividad Comercial")
    # autorizacion=fields.Char(string=" Número de Autorización")
    # fecha_autorizacion=fields.Date(string="Fecha de Autotización")
    cuenta_utilidad_recibo = fields.Many2one('account.account',string="Cuenta Utilidad en Recibos")

