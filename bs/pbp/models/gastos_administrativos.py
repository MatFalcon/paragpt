from odoo import models, fields, api, exceptions


class GastosAdministrativos(models.Model):
    _name = "pbp.gastos_administrativos"
    _description = "Modelo de Gastos Administrativos"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'id'

    name = fields.Char('Secuencia')
    partner_id = fields.Many2one('res.partner', string="Partner", required=True, tracking=True)
    fecha_operacion = fields.Date(string="Fecha de Operación", default=fields.Date.today(), required=True, tracking=True)
    fecha_correccion = fields.Date(string="Fecha de Corrección", default=fields.Date.today(), required=True, tracking=True)
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(
        'res.currency', string="Moneda", default=lambda self: self.env.user.company_id.currency_id)
    motivo = fields.Char(string='Motivo', required=True, tracking=True)
    monto = fields.Monetary(string="Monto", required=True, tracking=True)
    state = fields.Selection(
        selection=[
            ('verificado', 'Verificado'),
            ('cancelado', 'Cancelado'),
            ('no_verificado','No Verificado')
        ], default="no_verificado", string="Status", required=True, tracking=True)
    invoice_id = fields.Many2one('account.move', string="Factura")

    def button_cancelar(self):
        for i in self:
            i.write({'state':'cancelado'})

    def button_verificar(self):
        for i in self:
            i.write({'state':'verificado'})
    @api.onchange("fecha_operacion")
    @api.depends("fecha_operacion")
    def onchangeFechaOperacion(self):
        for i in self:
            monto_jornal = self.env['mantenimiento_registro.jornal_mantenimiento'].search([('activo','=',True)])
            if monto_jornal:
                i.monto = monto_jornal.monto
            else:
                i.monto = 0
