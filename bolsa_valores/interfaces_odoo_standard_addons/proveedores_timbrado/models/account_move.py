from odoo import api, fields, models, exceptions
from datetime import datetime


class account_move(models.Model):
    _inherit = 'account.move'

    timbrado_id = fields.Many2one(comodel_name='proveedores_timbrado.timbrado', string='Timbrado del proveedor')
    fecha_vencimiento = fields.Date(string='Fecha vencimiento timbrado', compute='compute_deadline_timbrado')
    fecha_inicio = fields.Date(string='Fecha inicio de vigencia', compute='compute_deadline_timbrado')

    @api.onchange('timbrado_id')
    @api.depends('timbrado_id')
    def compute_deadline_timbrado(self):
        for r in self:
            if r.timbrado_id:
                r.fecha_vencimiento = r.timbrado_id.fin_vigencia
                r.fecha_inicio = r.timbrado_id.inicio_vigencia
            else:
                r.fecha_vencimiento = False
                r.fecha_inicio = False

    # @api.model
    # def create(self, vals):
    #     if vals.get('move_type') in ['in_invoice','in_refund'] and vals.get('timbrado_id') and vals.get('invoice_date'):
    #         timbrado_id = self.env['proveedores_timbrado.timbrado'].search([('id', '=', vals.get('timbrado_id'))])
    #         invoice_date = vals.get('invoice_date')
    #         if type(invoice_date) == str:
    #             invoice_date = datetime.strptime(vals.get('invoice_date'), '%Y-%m-%d').date()
    #         if timbrado_id.fin_vigencia < invoice_date or timbrado_id.inicio_vigencia > invoice_date:
    #             raise exceptions.ValidationError('Timbrado no valido')
    #         vals['timbrado_proveedor']=timbrado_id.name
    #     return super(account_move, self).create(vals)

    @api.model
    def create(self, vals):
        result = super(account_move, self).create(vals)
        for this in result:
            if this.timbrado_proveedor != this.timbrado_id.name: this.timbrado_proveedor = this.timbrado_id.name
        return result

    # def write(self, vals):
    #
    #     for r in self:
    #         if r.move_type in ['in_invoice', 'in_refund']:
    #             if vals.get('timbrado_id'):
    #                 if r.invoice_date:
    #                     timbrado_id = self.env['proveedores_timbrado.timbrado'].search([('id', '=', vals.get('timbrado_id'))])
    #                     if timbrado_id.fin_vigencia < r.invoice_date or timbrado_id.inicio_vigencia > r.invoice_date:
    #                         raise exceptions.ValidationError('Timbrado no valido')
    #                     vals['timbrado_proveedor'] = timbrado_id.name
    #             else:
    #                 timbrado = r.timbrado_id.name if r.timbrado_id else False
    #                 vals['timbrado_proveedor'] = timbrado
    #     return super(account_move, self).write(vals)

    def write(self, vals):
        result = super(account_move, self).write(vals)
        for this in self:
            if this.timbrado_proveedor != this.timbrado_id.name: this.timbrado_proveedor = this.timbrado_id.name
        return result
