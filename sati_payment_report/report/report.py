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
from odoo.addons.web.controllers.main import content_disposition

_logger = logging.getLogger(__name__)
import werkzeug


class ReportPayment(models.AbstractModel):
    _name = 'report.sati_payment_report.report_payment'
    _description = 'Payment Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['sati_payment_report.wizard'].browse(self.env.context.get('active_id'))
        start_date = data['form'].get('start_date')
        end_date = data['form'].get('end_date')
        payments = docs.get_payments()
        payments_grouped = {}
        journal_totals_currency = {}
        journal_totals_local = {}
        journal_totals_gs = {}
        journal_totals_usd = {}
        total_local = 0
        total_currency = 0
        total_totales = 0
        for payment in payments:
            if payment.journal_id.id not in payments_grouped:
                payments_grouped[payment.journal_id.id] = []
                journal_totals_local[payment.journal_id.id] = 0
                journal_totals_currency[payment.journal_id.id] = 0
                journal_totals_gs[payment.journal_id.id] = 0
                journal_totals_usd[payment.journal_id.id] = 0

            payments_grouped[payment.journal_id.id].append(payment)
            journal_totals_local[payment.journal_id.id] += payment.amount_local
            journal_totals_currency[payment.journal_id.id] += payment.amount_currency

            if payment.currency_id.name == 'PYG':
                journal_totals_gs[payment.journal_id.id] += payment.amount_local
            else:
                journal_totals_usd[payment.journal_id.id] += payment.amount_currency

            total_local += payment.amount_local
            total_currency += payment.amount_currency

            if payment.currency_id:
                if payment.currency_id.name == 'PYG':
                    total_totales += payment.amount_local

        journal_ids = self.env['account.journal'].browse(
            set(journal_totals_local.keys()).union(journal_totals_currency.keys()))

        return {
            'date_from': start_date,
            'date_to': end_date,
            'doc_ids': payments.ids,
            'doc_model': 'account.payment',
            'docs': payments,
            'data': data,
            'payments_grouped': payments_grouped,
            'journal_totals_currency': journal_totals_currency,
            'journal_totals_local': journal_totals_local,
            'journal_totals_gs': journal_totals_gs,
            'journal_ids': journal_ids,
            'total_local': total_local,
            'total_currency': total_currency,
            'total_totales': total_totales,
        }

    class DownloadXLS(http.Controller):
        @http.route('/getPaymentReport/<int:id>', auth='public')
        def generarXLSX(self, id=None, **kw):
            total_local = 0
            total_currency = 0
            total_local = 0
            total_currency = 0
            total_totales = 0
            gs = 0
            usd = 0
            record = request.env['sati_payment_report.wizard'].browse(id)
            payments = record.get_payments()
            # payments = record.get_payments().filtered(lambda p:p.id == 15651)
            payments_grouped = {}
            journal_totals_currency = {}
            journal_totals_local = {}
            journal_totals_gs = {}
            journal_totals_usd = {}
            for payment in payments:
                if payment.journal_id.id not in payments_grouped:
                    payments_grouped[payment.journal_id.id] = []
                    journal_totals_local[payment.journal_id.id] = 0
                    journal_totals_currency[payment.journal_id.id] = 0
                    journal_totals_gs[payment.journal_id.id] = 0
                    journal_totals_usd[payment.journal_id.id] = 0

                payments_grouped[payment.journal_id.id].append(payment)
                journal_totals_local[payment.journal_id.id] += payment.amount_local

                if payment.currency_id.name == 'PYG':
                    journal_totals_gs[payment.journal_id.id] += payment.amount_local
                else:
                    journal_totals_usd[payment.journal_id.id] += payment.amount_currency

            journal_ids = request.env['account.journal'].browse(
                set(journal_totals_local.keys()).union(journal_totals_currency.keys()))
            i = 3  # Start writing data from the fourth row because the first three rows will contain the report title and date range.
            fp = io.BytesIO()
            workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
            sheet = workbook.add_worksheet('Reporte de pagos')
            bold = workbook.add_format({'bold': True, 'fg_color': 'gray', 'align': 'center'})
            border = workbook.add_format({'border': 1})
            date_format = workbook.add_format({'num_format': 'dd-mm-yyyy'})
            red_format = workbook.add_format(({
                'fg_color': 'red',
                'font_color': 'white'
            }))
            merge_format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': 'gray'})
            sheet.set_column('A:E', 25)
            sheet.set_column('F:G', 35)

            # Write the report title and date range
            sheet.merge_range('A1:G1', 'Reporte de pagos', merge_format)
            sheet.merge_range('A2:G2',
                              'Fecha Desde: ' + str(record.start_date) + ' - Fecha Hasta: ' + str(record.end_date),
                              merge_format)
            sheet.write(2, 0, 'Fecha', bold)
            sheet.write(2, 1, 'Diario', bold)
            sheet.write(2, 2, 'Cliente', bold)
            sheet.write(2, 3, 'Factura', bold)
            sheet.write(2, 4, 'Recibo', bold)
            sheet.write(2, 5, 'Cheque', bold)
            sheet.write(2, 6, 'Cheque Vencimiento', bold)
            sheet.write(2, 7, 'Moneda', bold)
            sheet.write(2, 8, 'Documento', bold)
            sheet.write(2, 9, 'Pago de Factura', bold)
            sheet.write(2, 10, 'Monto moneda local', bold)
            sheet.write(2, 11, 'Monto moneda extranjera', bold)
            sheet.write(2, 12, 'Fecha de Operacion', bold)
            for journal in journal_ids:
                sheet.write(i, 0, journal.name, bold)
                i += 1

                for p in payments_grouped[journal.id]:
                    sheet.write(i, 12, p.date, date_format)
                    sheet.write(i, 1, p.journal_id.name)
                    sheet.write(i, 2, p.partner_id.name)
                    row = i

                    if p.reconciled_invoice_ids and not p.recibo_id:
                        for move in p.reconciled_invoice_ids:
                            sheet.write(row, 3, move.nro_factura)
                            row += 1
                    elif p.recibo_id:
                        for rec in p.recibo_id.pagos_facturas_ids:
                            for move in p.reconciled_invoice_ids:
                                if move.nro_factura == rec.invoice_id.name:
                                    receivable_line_inv = move.line_ids.filtered(
                                        lambda line: line.account_id.account_type == 'asset_receivable')[:1]
                                    receivable_line_payment = p.move_id.line_ids.filtered(
                                        lambda line: line.account_id.account_type == 'asset_receivable')
                                    partial_reconcile = record.env['account.partial.reconcile'].search(
                                        [('debit_move_id', '=', receivable_line_inv.id),
                                         ('credit_move_id', '=', receivable_line_payment.id)])
                                    sheet.write(row, 3, move.nro_factura)
                                    sheet.write(i, 4, p.recibo_id.name)
                                    sheet.write(row, 9,
                                                partial_reconcile.credit_amount_currency if partial_reconcile else rec.monto)
                                    if p.currency_id.name != 'PYG':
                                        p.amount_currency = partial_reconcile.credit_amount_currency
                                        journal_totals_currency[p.journal_id.id] += p.amount_currency
                                        total_currency += p.amount_currency
                                        sheet.write(i, 11, p.amount_currency)

                                    row += 1
                    if p.received_third_check_ids:
                        for c in p.received_third_check_ids:
                            sheet.write(i, 5, c.number)
                            sheet.write(i, 6, c.payment_date, date_format)
                            sheet.write(i, 10, c.amount)
                    sheet.write(i, 7, p.currency_id.name)
                    sheet.write(i, 8, p.name)
                    sheet.write(i, 10, p.amount_local)

                    if p.payment_type == 'inbound':
                        if p.recibo_id:
                            sheet.write(i, 0, p.recibo_id.fecha, date_format)
                        else:
                            sheet.write(i, 0, p.date, date_format)

                    total_local += p.amount_local

                    if p.currency_id:
                        if p.currency_id.name == 'PYG':
                            total_totales += p.amount_local
                    i = row
                # Write the section title
            sheet.merge_range('A' + str(i + 1) + ':C' + str(i + 1), 'Totales por Diario', merge_format)
            i += 1

            sheet.write(i, 0, 'Diario', bold)
            sheet.write(i, 1, 'Total conversion moneda local', bold)
            sheet.write(i, 2, 'Total moneda extranjera', bold)
            sheet.write(i, 3, 'Total moneda local', bold)

            i += 1
            # Now write the totals for each journal
            for journal in journal_ids:
                sheet.write(i, 0, journal.name)
                sheet.write(i, 1, journal_totals_local[journal.id])
                sheet.write(i, 2, journal_totals_currency[journal.id])
                sheet.write(i, 3, journal_totals_gs[journal.id])

                i += 1
            sheet.write(i, 0, 'Totales por Diario', bold)
            sheet.write(i, 1, total_local)
            sheet.write(i, 2, total_currency)
            sheet.write(i, 3, total_totales)

            workbook.close()
            fp.seek(0)
            return request.make_response(fp.read(),
                                         [('Content-Type',
                                           'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                                          ('Content-Disposition', content_disposition('reporte_pagos.xlsx'))])
