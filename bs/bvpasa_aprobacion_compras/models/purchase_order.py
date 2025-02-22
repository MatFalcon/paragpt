from odoo import models, fields, api, exceptions


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    aprobado = fields.Boolean(string="Aprobado", default=False, copy=False, tracking=True)
    usuario_aprobador = fields.Many2one('res.users', string="Usuario aprobador")
    puede_aprobar = fields.Boolean(string="Puede Aprobar", default=False, copy=False, compute="_getPuedeAprobar")

    @api.depends('usuario_aprobador')
    @api.onchange('usuario_aprobador')
    def _getPuedeAprobar(self):
        if self.usuario_aprobador != self.env.user:
            self.update({'puede_aprobar':True})
        else:
            self.update({'puede_aprobar':False})

    def _approval_allowed(self):
        """Returns whether the order qualifies to be approved by the current user"""
        self.ensure_one()
        val = (
                self.company_id.po_double_validation == 'one_step'
                or (self.company_id.po_double_validation == 'two_step'
                    and self.amount_total < self.env.company.currency_id._convert(
                    self.company_id.po_double_validation_amount, self.currency_id, self.company_id,
                    self.date_order or fields.Date.today()))
                or self.aprobado)
        return val

    def button_approve(self, force=False):
        limite = (self.company_id.po_double_validation == 'two_step'
                    and self.amount_total < self.env.company.currency_id._convert(
                    self.company_id.po_double_validation_amount, self.currency_id, self.company_id,
                    self.date_order or fields.Date.today()))
        if not self.aprobado and not limite:
            self.write({'aprobado': True, 'usuario_aprobador': self.env.user.id})
            return
        result = super(PurchaseOrder, self).button_approve(force=force)
        self._create_picking()
        return result
