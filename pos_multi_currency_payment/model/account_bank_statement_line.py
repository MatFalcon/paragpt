# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import logging

_logger = logging.getLogger(__name__)

class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    currency_pago = fields.Many2one('res.currency')
    amount_pago = fields.Monetary(currency_field='currency_pago')

    def fast_counterpart_creation(self):
        # from_pos = False
        # for st_line in self:
        #     if st_line.amount_currency != 0 and st_line.pos_statement_id and st_line.pos_statement_id.create_uid and st_line.pos_statement_id.create_uid.company_id and st_line.pos_statement_id.create_uid.company_id.currency_id and st_line.pos_statement_id.create_uid.company_id.currency_id.id != st_line.currency_id.id:
        #         from_pos= True
        # if from_pos == True:
        #     for st_line in self:
        #         vals = {}
        #         if st_line.pos_statement_id and st_line.pos_statement_id.create_uid and st_line.pos_statement_id.create_uid.company_id and st_line.pos_statement_id.create_uid.company_id.currency_id and st_line.pos_statement_id.create_uid.company_id.currency_id.id != st_line.currency_id.id:
        #             vals = {
        #                 'name': st_line.name,
        #                 'debit': st_line.amount_currency < 0 and -st_line.amount_currency or 0.0,
        #                 'credit': st_line.amount_currency > 0 and st_line.amount_currency or 0.0,
        #                 'account_id': st_line.account_id.id,
        #                 'currency_id': st_line.currency_id.id,
        #                 'amount_currency': st_line.amount_currency,
        #
        #             }
        #         else:
        #             vals = {
        #                 'name': st_line.name,
        #                 'debit': st_line.amount < 0 and -st_line.amount or 0.0,
        #                 'credit': st_line.amount > 0 and st_line.amount or 0.0,
        #                 'account_id': st_line.account_id.id,
        #             }
        #         st_line.process_reconciliation(new_aml_dicts=[vals])
        # else:
            return super(account_bank_statement_line, self).fast_counterpart_creation()

