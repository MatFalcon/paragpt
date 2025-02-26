from odoo import api, fields, models


class Resolucion90Wizard(models.Model):
    _inherit = 'resolucion_90.wizard'

    @api.model
    def obtener_facturas(self, anho, mes, tipo):
        result = super(Resolucion90Wizard, self).obtener_facturas(anho, mes, tipo)
        if tipo == 'compras':
            result = result.filtered(lambda x: not x.es_factura_exterior)
        return result
