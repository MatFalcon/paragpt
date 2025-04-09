# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    saldo_anticipo = fields.Float(string="Saldo de anticipos del contacto",compute="_get_anticipos")
    anticipo_lines = fields.Many2many('account.move.line',string="Anticipos",compute="_get_anticipos")
    pago_anticipo = fields.Boolean(string="Pago de anticipo", compute="_es_anticipo",store=True)

    @api.depends('saldo_anticipo')
    def _es_anticipo(self):
        for rec in self:
            if rec.journal_id.anticipo:
                rec.pago_anticipo = True
            else:
                rec.pago_anticipo = False

    @api.depends('partner_id','journal_id')
    def _get_anticipos(self):
        for rec in self:
            rec.saldo_anticipo = 0
            rec.anticipo_lines = False
            if rec.partner_id and rec.journal_id:
                saldo_anticipo_list = self.env['account.move.line'].search([('account_id','=',rec.journal_id.default_account_id.id),
                                                                           ('partner_id','=',rec.partner_id.id)])
                if len(saldo_anticipo_list) > 0:
                    rec.saldo_anticipo = sum(l.balance for l in saldo_anticipo_list)
                    anticipos_list = list()
                    for p in saldo_anticipo_list:
                        anticipos_list.append(p.id)
                    rec.anticipo_lines =[(6, 0, anticipos_list)]


