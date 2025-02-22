from odoo import api, models, fields


class ProductTemplateCustom(models.Model):
    _inherit = 'product.template'

    _sql_contraints = [
        'uniq_contrato_descripcion_pbp',
        'unique(contrato_descripcion_pbp)',
        'Ya existe un producto con el mismo Contrato descripción PBP',
    ]

    porcentaje_arancel = fields.Float()
    contrato_descripcion_pbp = fields.Char(string='Contrato descripción PBP')
    tipo_renta = fields.Selection(selection=[
            ('fija', 'Fija'),
            ('variable', 'Variable'),
        ], default="", string="Tipo de Renta")

    @api.onchange('contrato_descripcion_pbp')
    def _onchange_contrato_descripcion(self):
        self._update_novedades(self.product_variant_id)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        self._update_novedades(record.product_variant_id)
        return record

    def _update_novedades(self, product_variant_id):
        if not self.contrato_descripcion_pbp:
            return
        domain = [('contrato_descripcion', '=', self.contrato_descripcion_pbp)]
        novedades = self.env['pbp.novedades'].search(domain)
        novedades.write({'product_id': product_variant_id})


class ProductCustom(models.Model):
    _inherit = 'product.product'

    _sql_contraints = [
        'uniq_contrato_descripcion_pbp',
        'unique(contrato_descripcion_pbp)',
        'Ya existe un producto con el mismo Contrato descripción PBP',
    ]

    porcentaje_arancel = fields.Float(related='product_tmpl_id.porcentaje_arancel', readonly=False)
    contrato_descripcion_pbp = fields.Char(related='product_tmpl_id.contrato_descripcion_pbp', readonly=False)
