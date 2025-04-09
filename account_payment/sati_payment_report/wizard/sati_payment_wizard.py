# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
import time, collections
import io
from odoo.exceptions import ValidationError
import xlsxwriter
import logging
from datetime import date

import base64
import xlwt
import base64
import xlsxwriter
from io import StringIO
from odoo import http, _
from odoo.http import request
from odoo.addons.web.controllers.main import  content_disposition

_logger = logging.getLogger(__name__)
import werkzeug

from odoo import api, fields, models


class ReportWizard(models.TransientModel):
    _name = 'sati_payment_report.wizard'

    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date', required=True)
    journal_ids = fields.Many2many('account.journal', string='Journal', required=True,
                                  )
    partner_ids = fields.Many2many('res.partner', string='Partners')
    type = fields.Selection(selection=[('inbound', 'Cobro'), ('outbound', 'Pago')], string="Type")

    def get_domain(self):
        domain = [
            '|',
            # Caso 1: Existe recibo y se filtra por recibo_id.fecha
            ('recibo_id.fecha', '>=', self.start_date),
            # Caso 2: No existe recibo y se filtra por date
            ('date', '>=', self.start_date),
            '|',
            ('recibo_id.fecha', '<=', self.end_date),
            ('date', '<=', self.end_date),
            ('journal_id', 'in', self.journal_ids.ids),
            ('state', '=', 'posted'),
        ]
        if self.type == 'inbound':
            domain.append(('payment_type', '=', 'inbound'))
        elif self.type == 'outbound':
            domain.append(('payment_type', '=', 'outbound'))
        if self.partner_ids:
            domain.append(('partner_id', 'in', self.partner_ids.ids))

        return domain

    def _get_default_journals(self):
        payment = self.env['account.payment'].search([])
        return [(6, 0, payment.journal_id.ids)] if payment else False

    def get_payments(self):
        domain = self.get_domain()
        payments = self.env['account.payment'].search(domain, order='date')

        return payments

    def action_print_report(self):
        data = {
            'model': self._name,
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'journal_ids': self.journal_ids.ids,
                'partner_ids': self.partner_ids.ids,
            },
        }
        return self.env.ref('sati_payment_report.report_action').report_action(self, data=data)

    def action_print_report_xlsx(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/getPaymentReport/' + str(self.id),
            'target': 'self'
        }
