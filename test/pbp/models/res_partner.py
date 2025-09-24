from odoo import api, models, fields


class PartnerCustom(models.Model):
    _inherit = 'res.partner'

    _sql_contraints=[
        'uniq_id_cliente_pbp',
        'unique(id_cliente_pbp)',
        'Ya existe un partner con el mismo ID cliente PBP',
    ]

    id_cliente_pbp = fields.Integer(string='ID cliente PBP', copy=False)

    casa_bolsa = fields.Boolean(string="Casa de Bolsa", copy=False, default=False)
    entidad_publica = fields.Boolean(string="Entidad pública", copy=False, default=False)

    @api.onchange('id_cliente_pbp')
    def _onchange_id_cliente_pbp(self):
        self.update_novedades(self._origin.id)

    @api.model
    def create(self, vals):
        record = super().create(vals)
        self.update_novedades(record.id)
        return record

    def update_novedades(self, partner_id):
        if not self.id_cliente_pbp:
            return False

        novedades = self.env['pbp.novedades'].search([('cliente_id', '=', self.id_cliente_pbp)])
        novedades.write({'partner_id': partner_id})

        novedades_sen = self.env['pbp.novedades_sen'].search([('persona_id', '=', self.id_cliente_pbp)])
        novedades_sen.write({'partner_id': partner_id})

        novedades_series = self.env['pbp.novedades_series'].search([('persona_id', '=', self.id_cliente_pbp)])
        novedades_series.write({'partner_id': partner_id})

        return True
