# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError
from odoo.addons import decimal_precision as dp
from num2words import num2words

class SaleInvoiceTermsConditions(models.Model):
    _name = 'sale.invoice.terms.conditions'
    _description = 'Invoice Terms Conditions'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']


    name = fields.Char(string='Name')
    user_id = fields.Many2one('res.users',string="Responsible",tracking=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', ondelete='cascade', index=True,tracking=True)
    date_deadline = fields.Date(string='Date deadline',tracking=True)
    state = fields.Selection(selection=[('pending','Pending'),('done','Done')],string="State",default="pending",tracking=True)
    sale_invoice_term_id = fields.Many2one('sale.invoice.terms', string="Invoice term",tracking=True)
    partner_id = fields.Many2one(related='sale_order_id.partner_id',store=True,tracking=True)
    analytic_account_id = fields.Many2one(related='sale_order_id.analytic_account_id',store=True,tracking=True)
    invoice_id = fields.Many2one(related='sale_invoice_term_id.invoice_id',store=True,tracking=True)
    condition_activity_type_id = fields.Many2one('mail.activity.type',string="Activity type",tracking=True)

    def action_view_condition(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'sale.invoice.terms.conditions',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
    def set_done(self):
        for rec in self:
            rec.state = 'done'

