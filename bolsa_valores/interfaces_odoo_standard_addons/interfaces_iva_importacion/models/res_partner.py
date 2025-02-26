from odoo import api, fields, models,exceptions


class ResPartner(models.Model):
    _inherit = 'res.partner'

    es_proveedor_por_defecto_exterior = fields.Boolean(string='Es Proveedor por Defecto del Exterior', default=False)

    @api.constrains('es_proveedor_por_defecto_exterior')
    def _check_es_proveedor_por_defecto_exterior(self):
        for this in self:
            if this.es_proveedor_por_defecto_exterior and len(self.search([('es_proveedor_por_defecto_exterior', '=', True), ('id', '!=', this.id)])):
                raise exceptions.ValidationError("Solo debe de haber un Proveedor por defecto del exterior")
