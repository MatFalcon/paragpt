# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError

class asignacion(models.Model):
    _inherit = 'account.recibo'

    def retornar_asignacion(self):
        view = self.env.ref('account_cobros_py.wizard_asignacion_facturasc')
        invoices = self.env['account.move'].search([('no_ver_factura_pago', '=', False), ('state', '=', 'posted'),('payment_state', 'in', ('not_paid','partial')),
                                                       ('partner_id', 'child_of', self.partner_id.id),
                                                       ('move_type', 'in', ('out_refund','out_invoice')),
                                                       ('currency_id', '=', self.currency_id.id)],
                                                      order='invoice_date asc', limit=10)
        if len(invoices) > 0:
            wiz = self.env['account_cobros_py.wizard_asignacion_c'].create({'invoice_ids': [(6, 0, invoices.ids)],
                                                                           'recibo_id': self.id,
                                                                           'partner_id': self.partner_id.id,
                                                                           'currency_id': self.currency_id.id})
        else:
            wiz = self.env['account_cobros_py.wizard_asignacion_c'].create({'recibo_id': self.id})

        return {
            'name': 'Asignar facturas',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account_cobros_py.wizard_asignacion_c',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }

    def eliminar_asignacion(self):
        if self.pagos_facturas_ids:
            for f in self.pagos_facturas_ids:
                f.invoice_id.no_ver_factura_recibo = False
            self.pagos_facturas_ids.unlink()

class wizard_asignacionc(models.TransientModel):

    _name = 'account_cobros_py.wizard_asignacion_c'


    recibo_id = fields.Many2one('account.recibo',string="Recibo")

    invoice_ids = fields.Many2many('account.move',string="Facturas")
    partner_id = fields.Many2one('res.partner')
    currency_id = fields.Many2one('res.currency')


    def limpiar(self):
        self.ensure_one()
        self.invoice_ids = None
        return {
            "type": "set_scrollTop",
        }

    def procesar(self):
        self.ensure_one()
        if len(self.invoice_ids) > 0:
            for inv in self.invoice_ids:
                inv.no_ver_factura_pago=True
                values= {'invoice_id':inv.id,'residual':inv.amount_residual,'monto':inv.amount_residual,'amount_total':inv.amount_total_in_currency_signed}
                self.recibo_id.pagos_facturas_ids = [((0, 0, values))]
                self.recibo_id.setear_currency_invoice()
                try:
                    self.recibo_id._actualizar_monto_retencion()
                except:
                    continue


