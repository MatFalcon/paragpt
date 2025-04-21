from odoo import api, fields, models


class NovedadesSeries(models.Model):
    _name = 'pbp.novedades_series'
    _order = 'state, fecha desc'

    id_operacion = fields.Integer(required=True, string='ID Operación')
    tipo_contrato_descripcion = fields.Char(required=True, string='Tipo Contrato Descripción')

    persona_id = fields.Integer(required=True)
    fecha = fields.Date(required=True)
    valor_nominal = fields.Float(required=True)
    cantidad = fields.Integer(required=True)

    volumen = fields.Float(readonly=1)
    total_arancel = fields.Float(readonly=1)
    iva = fields.Float(string='IVA', readonly=1)
    total = fields.Float(readonly=1)
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

    @api.onchange("valor_nominal", "cantidad")
    def _onchange_valor_nominal(self):
        for record in self:
            if record.valor_nominal and record.cantidad:
                record.volumen = record.valor_nominal * record.cantidad

                record.total_arancel = (record.volumen / 100) * 0.02
                record.iva = round(record.total_arancel * 0.1, 2)
                record.total = record.iva + record.total_arancel