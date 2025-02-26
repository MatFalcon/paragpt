from odoo import models, fields,api

class Resolucion(models.Model):
    _name = 'resolucion'
    _description = 'Resoluciones'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Nombre", required=True, tracking=True)
    cliente = fields.Many2one('res.partner', string="Cliente", required=True, tracking=True)
    fecha_creacion = fields.Date(string="Fecha de Creación", default=fields.Date.context_today, required=True, tracking=True)
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento", required=True, tracking=True)
    codigo = fields.Char(string="Código", required=True, tracking=True)
    pbp_novedades_sen_id = fields.Many2one('pbp.novedades_sen', string='Custodia Anual')
    novedades_sen_ids = fields.One2many('pbp.novedades_sen', 'resolucion_id', string='Novedades Sen', tracking=True)


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

        return True
