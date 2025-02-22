from odoo import api, fields, models


class NovedadesSeries(models.Model):
    _name = 'pbp.novedades_series'
    _order = 'state, fecha desc'

    id_operacion = fields.Integer(required=True, string='ID Operación')
    tipo_contrato_descripcion = fields.Char(required=True, string='Tipo Contrato Descripción')

    persona_id = fields.Integer(required=True)
    fecha = fields.Date(required=True)
    valor_nominal = fields.Integer(required=True)
    cantidad = fields.Integer(required=True)

    volumen = fields.Float()
    total_arancel = fields.Float()
    iva = fields.Float(string='IVA')
    total = fields.Float()
    tipo = fields.Selection(selection=[('compra','Compra'),('venta','venta')], string="Tipo")

    state = fields.Selection(
        selection=[
            ('inactivo', 'Inactivo'),
            ('pendiente', 'Pendiente'),
            ('draft', 'Draft'),
            ('publicado', 'Publicado'),
        ],
        required=True,
        default='pendiente',
        string='Estado',
    )

    partner_id = fields.Many2one('res.partner', string="Cliente")
    currency_id = fields.Many2one('res.currency', required=True, string="Moneda")
    product_id = fields.Many2one('product.product', string='Producto')
    invoice_id = fields.Many2one('account.move')

    @api.model
    def create(self, vals):
        record = super().create(vals)
        self.env['pbp.novedades_pbp'].create([{'novedades_series_id': record.id}])
        return record

    def marcar_como_inactivo(self):
        self.state = 'inactivo'
        dialog = self.env['pbp.dialog.box'].sudo().search([])[-1]
        return {
            'type':'ir.actions.act_window',
            'name':'Message',
            'res_model':'pbp.dialog.box',
            'view_mode':'form',
            'target':'new',
            'res_id': dialog.id
        }

    #def calcular_valores(self):
    #    novedades = self.env['pbp.novedades_series'].search([['state', '=', 'pendiente']])
    #    for novedad in novedades:
    #        if novedad.tipo_contrato_descripcion == 'Serie Renta Variable Acción':
    #            novedad.total_arancel = novedad.volumen * 0.02
    #            novedad.iva = (10 * novedad.total_arancel) / 100
    #            novedad.total = novedad.total_arancel + novedad.iva
    #    return True
