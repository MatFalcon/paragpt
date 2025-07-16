# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
from num2words import num2words

class SaleInvoiceTerms(models.Model):
    _name = 'sale.invoice.terms'
    _description = 'Invoice Terms'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    def open_terms_conditions_wizard(self):
        return {
            'name': _('Assign conditions'),
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.terms.conditions.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_invoice_term_id': self.id,'default_sale_order_id': self.sale_order_id.id},
        }


    name = fields.Char(string='Name', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'),tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade', index=True)
    invoice_date = fields.Date(string='Invoice Date',tracking=True)
    invoice_amount = fields.Float(string='Invoice Amount',tracking=True)
    state = fields.Selection(selection=[('pending','Pending to invoice'),('ready','Ready to be invoiced'),('invoiced','Invoiced')],string="Invoice state", default="pending")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    partner_id = fields.Many2one(related='sale_order_id.partner_id',store=True)
    analytic_account_id = fields.Many2one(related='sale_order_id.analytic_account_id',store=True,tracking=True)
    provition_move_id = fields.Many2one('account.move',string="Provition account move",tracking=True)
    provition_cancel_move_id = fields.Many2one('account.move',string="Provition cancel account move",tracking=True)
    invoice_term_condition_ids = fields.One2many('sale.invoice.terms.conditions','sale_invoice_term_id',tracking=True)
    generate_account_move = fields.Boolean('Generar asiento contable',tracking=True)

    def action_view_invoice_term(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.invoice.terms',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def generate_cancel_provition_move(self):
        self.ensure_one()
        AccountMove = self.env['account.move']
        if not self.provition_cancel_move_id and self.provition_move_id:
            original_move = self.provition_move_id
            analytic_account_id = self.sale_order_id.analytic_account_id.id if self.sale_order_id.analytic_account_id else False
            line_vals = []

            for line in original_move.line_ids:
                # Invertir valores de débito y crédito
                debit, credit = line.credit, line.debit
                line_vals.append((0, 0, {
                    'name': line.name,
                    'account_id': line.account_id.id,
                    'debit': debit,
                    'credit': credit,
                    'amount_currency': -line.amount_currency,
                    'currency_id': line.currency_id.id,
                    'analytic_account_id': analytic_account_id,
                }))

            move_vals = {
                'ref': 'Cancelación: ' + original_move.ref,
                'date': fields.Date.today(),
                'journal_id': original_move.journal_id.id,
                'line_ids': line_vals,
            }
            cancel_move = AccountMove.create(move_vals)
            cancel_move.post()
            self.provition_cancel_move_id = cancel_move.id


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.invoice.terms.sequence') or _('New')
        result = super(SaleInvoiceTerms, self).create(vals)
        return result
    def control_condition_state_invoice(self):
        if self.invoice_term_condition_ids:
            if any(condition.state != 'done' for condition in self.invoice_term_condition_ids):
                raise ValidationError(_('Only a term with conditions in state done can be invoiced'))
    def action_generate_invoice(self):
        self.ensure_one()
        self.control_condition_state_invoice()
        action = self.env.ref('sale.action_view_sale_advance_payment_inv').read()[0]
        action['context'] = {
            'active_id': self.sale_order_id.id,
            'active_ids': [self.sale_order_id.id],
            'active_model': 'sale.order',
            'default_amount': self.invoice_amount,
            'default_advance_payment_method': 'delivered',
            'invoice_term_id': self.id,  # agrega el ID del invoice term al contexto
        }
        return action