from odoo import api, fields, models

from odoo.addons.pbp.facturas.generador import generar_facturas
from odoo.addons.pbp.models.novedades_series import NovedadesSeries

from odoo.addons.pbp.models.novedades import Novedades


class NovedadesPBP(models.Model):
    _name = 'pbp.novedades_pbp'
    _order = 'fecha desc'
    _rec_name = 'id'

    novedades_default_id = fields.Many2one('pbp.novedades', 'Novedad')
    novedades_series_id = fields.Many2one('pbp.novedades_series', string='Novedad Sistema Tradicional')
    es_sistema_tradicional = fields.Boolean(compute='_compute_es_sistema_tradicional', store=True)

    tipo_contrato = fields.Char(compute='_compute_tipo_contrato', store=True)
    fecha = fields.Date(compute='_compute_fecha', store=True, string="Fecha")
    partner_id = fields.Many2one('res.partner', compute='_compute_partner_id', store=True, string="Cliente")
    product_id = fields.Many2one('product.product', compute='_compute_product_id', store=True, string='Producto')
    currency_id = fields.Many2one('res.currency', compute='_compute_currency_id', store=True, string="Moneda")
    invoice_id = fields.Many2one('account.move', compute='_compute_invoice_id', string='Factura')

    state = fields.Selection(
        compute='_compute_state',
        selection=[
            ('inactivo', 'Inactivo'),
            ('pendiente', 'Pendiente'),
            ('draft', 'Draft'),
            ('publicado', 'Publicado'),
        ],
        required=True,
        default='pendiente',
        store=True,
        string='Estado',
    )

    total = fields.Float(compute='_compute_total', store=True)

    def get_child_novedad(self, novedad):
        if novedad.novedades_default_id:
            return novedad.novedades_default_id
        elif novedad.novedades_series_id:
            return novedad.novedades_series_id

    @api.depends('novedades_default_id.partner_id', 'novedades_series_id.partner_id')
    def _compute_partner_id(self):
        for novedad in self:
            child = self.get_child_novedad(novedad)
            if child:
                novedad.partner_id = child.partner_id

    @api.depends('novedades_default_id.product_id', 'novedades_series_id.product_id')
    def _compute_product_id(self):
        for novedad in self:
            child = self.get_child_novedad(novedad)
            if child:
                novedad.product_id = child.product_id

    @api.depends('novedades_default_id.currency_id', 'novedades_series_id.currency_id')
    def _compute_currency_id(self):
        for novedad in self:
            child = self.get_child_novedad(novedad)
            if child:
                novedad.currency_id = child.currency_id

    def _compute_invoice_id(self):
        for novedad in self:
            child = self.get_child_novedad(novedad)
            if child:
                novedad.invoice_id = child.invoice_id

    @api.depends('novedades_default_id.contrato_tipo_descripcion', 'novedades_series_id.tipo_contrato_descripcion')
    def _compute_tipo_contrato(self):
        for novedad in self:
            if novedad.novedades_default_id:
                novedad.tipo_contrato = novedad.novedades_default_id.contrato_tipo_descripcion
            elif novedad.novedades_series_id:
                novedad.tipo_contrato = novedad.novedades_series_id.tipo_contrato_descripcion

    @api.depends('novedades_default_id.fecha_operacion', 'novedades_series_id.fecha')
    def _compute_fecha(self):
        for novedad in self:
            if novedad.novedades_default_id:
                novedad.fecha = novedad.novedades_default_id.fecha_operacion
            elif novedad.novedades_series_id:
                novedad.fecha = novedad.novedades_series_id.fecha

    @api.depends('novedades_default_id.state', 'novedades_series_id.state')
    def _compute_state(self):
        for novedad in self:
            child = self.get_child_novedad(novedad)
            if child:
                novedad.state = child.state

    @api.depends('novedades_default_id.total', 'novedades_series_id.total')
    def _compute_total(self):
        for novedad in self:
            if novedad.novedades_default_id:
                novedad.total = novedad.novedades_default_id.subtotal
            elif novedad.novedades_series_id:
                novedad.total = novedad.novedades_series_id.total

    @api.depends('novedades_series_id')
    def _compute_es_sistema_tradicional(self):
        for novedad in self:
            novedad.es_sistema_tradicional = bool(novedad.novedades_series_id)

    def generar_facturas(self, records=None):
        novedades_default = []
        novedades_series = []

        # TODO: reducir condicionales y ciclos
        if records and isinstance(records, Novedades):
            novedades_default = records.read((set(self.env['pbp.novedades']._fields)))
        elif records and isinstance(records, NovedadesSeries):
            novedades_series = records.read((set(self.env['pbp.novedades_series']._fields)))
        elif records:
            for record in records:
                if record.novedades_default_id:
                    obj = record.novedades_default_id.read((set(self.env['pbp.novedades']._fields)))[0]
                    novedades_default.append(obj)
                elif record.novedades_series_id:
                    obj = record.novedades_series_id.read((set(self.env['pbp.novedades_series']._fields)))[0]
                    novedades_series.append(obj)
        else:
            novedades_default = self.env['pbp.novedades'].search_read([
                ['state', '=', 'pendiente'],
                #['fecha_operacion', '>=', from_date],
                #['fecha_operacion', '<=', to_date],
            ])
            novedades_series = self.env['pbp.novedades_series'].search_read([
                ['state', '=', 'pendiente'],
                ['total', '>', 0],
                #['fecha', '>=', from_date],
                #['fecha', '<=', to_date],
            ])

        novedades = []
        if novedades_default:
            novedades += [novedad for novedad in novedades_default if novedad['state'] == 'pendiente']
        if novedades_series:
            novedades += [novedad for novedad in novedades_series if novedad['state'] == 'pendiente']

        data = generar_facturas(self.env, novedades)

        error_msg = ''
        if (
            data.get('novedades_sin_partners_ids') or
            data.get('novedades_sin_productos_ids') or
            data.get('novedades_series_sin_partners_ids') or
            data.get('novedades_series_sin_productos_ids')
        ):
            error_msg = 'No se pudieron generar algunas facturas debido a datos faltantes en Novedades.'

        dialog = self.env['pbp.dialog.box'].sudo().create({
            'error_msg': error_msg,
            'novedades_sin_partners_ids': data.get('novedades_sin_partners_ids', []),
            'novedades_sin_productos_ids':  data.get('novedades_sin_productos_ids', []),
            'novedades_sin_cuentas_ids':  data.get('novedades_sin_cuentas_ids', []),
            'invoice_ids': data.get('facturas_ids', []),
            'novedades_publicadas_ids': data.get('novedades_publicadas_ids', []),

            'novedades_series_sin_partners_ids': data.get('novedades_series_sin_partners_ids', []),
            'novedades_series_sin_productos_ids': data.get('novedades_series_sin_productos_ids', []),
            'novedades_series_sin_cuentas_ids': data.get('novedades_series_sin_cuentas_ids', []),
            'invoice_series_ids': data.get('facturas_series_ids', []),
            'novedades_series_publicadas_ids': data.get('novedades_series_publicadas_ids', []),
        })
        return{
            'type':'ir.actions.act_window',
            'name':'Message',
            'res_model':'pbp.dialog.box',
            'view_mode':'form',
            'target':'new',
            'res_id': dialog.id
        }
