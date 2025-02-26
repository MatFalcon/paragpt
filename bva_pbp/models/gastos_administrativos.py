from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError


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
    motivo = fields.Selection(
        selection=[
            ('1', 'Modificación de comitente'),
            ('2', 'Anulación de operaciones fuera de rueda ST y SEN'),
            ('3', 'Certificados de asamblea'),
            ('4', 'Certificado de titularidad'),
            ('5', 'Corrección de boletas')
        ],
        string='Motivo',
        default='1',
        required=True,
        tracking=True
    )
    monto = fields.Monetary(string="Monto", compute="_compute_monto", store=True, tracking=True)
    state = fields.Selection(
        selection=[
            ('verificado', 'Verificado'),
            ('cancelado', 'Cancelado'),
            ('no_verificado','No Verificado')
        ], default="no_verificado", string="Status", required=True, tracking=True)
    invoice_id = fields.Many2one('account.move', string="Factura")
    observacion = fields.Text(string="Observacion")
    def unlink(self):
        # Validar que no se pueda eliminar si el estado es "verificado"
        for record in self:
            if record.state == 'verificado':
                raise ValidationError("No se puede eliminar un registro que está en estado 'Verificado'.")
        return super(GastosAdministrativos, self).unlink()

    def button_cancelar(self):
        for i in self:
            i.write({'state':'cancelado'})

    def button_verificar(self):
        for i in self:
            i.write({'state':'verificado'})

    def button_set_to_draft(self):
        for i in self:
            i.write({'state':'no_verificado'})
    @api.depends('motivo')
    def _compute_monto(self):
        for rec in self:
            jornal = self.env.company.jornal
            if not jornal:
                rec.monto = 0
            else:
                if rec.motivo == '1':  # Modificación de comitente
                    rec.monto = jornal
                elif rec.motivo == '2':  # Anulación de operaciones fuera de rueda ST y SEN
                    rec.monto = 2 * jornal
                elif rec.motivo == '3':  # Certificados de asamblea
                    rec.monto = jornal
                elif rec.motivo == '4':  # Certificado de titularidad
                    rec.monto = jornal
                elif rec.motivo == '5':  # Corrección de boletas
                    rec.monto = 2 * jornal
                else:
                    rec.monto = 0