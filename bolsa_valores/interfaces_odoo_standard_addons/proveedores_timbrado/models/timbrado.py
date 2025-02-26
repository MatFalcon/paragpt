from odoo import api, fields, models


class Timbrado(models.Model):
    _name = 'proveedores_timbrado.timbrado'
    _description = 'Timbrado de un proveedor en contabilidad'

    name = fields.Char(string='Numero de Timbrado')
    inicio_vigencia = fields.Date(string='Fecha de inicio de vigencia', default=fields.Date.today(), required=True)
    fin_vigencia = fields.Date(string='Fecha de fin de vigencia', required=True)
    rango_inicial = fields.Char('Número de factura inicial')
    rango_final = fields.Char('Número de factura final')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Proveedor')
    

    
