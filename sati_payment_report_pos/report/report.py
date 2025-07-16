# -*- coding: utf-8 -*-
from odoo import models, api, fields
import io, xlsxwriter
from odoo.http import request, content_disposition
import logging
from odoo import http

_logger = logging.getLogger(__name__)

class ReportPaymentPOSExtension(models.AbstractModel):
    _inherit = 'report.sati_payment_report.report_payment'

    @api.model
    def _get_report_values(self, docids, data=None):
        # Obtiene los valores base llamando al super
        base_values = super(ReportPaymentPOSExtension, self)._get_report_values(docids, data=data)
        wizard = self.env['sati_payment_report.wizard'].browse(self.env.context.get('active_id'))

        pos_payments = wizard.get_pos_payments() if hasattr(wizard, 'get_pos_payments') else self.env['pos.payment']

        # Combina los pagos de account.payment y pos.payment usando concatenación de listas
        all_payments = list(base_values['docs']) + list(pos_payments)

        # Recalcula las agrupaciones y totales incluyendo los pagos POS
        payments_grouped = {}
        journal_totals_currency = {}
        journal_totals_local = {}
        journal_totals_gs = {}
        journal_totals_usd = {}
        total_local = 0
        total_currency = 0
        total_totales = 0

        for payment in all_payments:
            if payment._name == 'pos.payment':
                jid = payment.payment_method_id.journal_id.id
            else:
                jid = payment.journal_id.id
            if jid not in payments_grouped:
                payments_grouped[jid] = []
                journal_totals_local[jid] = 0
                journal_totals_currency[jid] = 0
                journal_totals_gs[jid] = 0
                journal_totals_usd[jid] = 0

            payments_grouped[jid].append(payment)
            journal_totals_local[jid] += payment.amount_local
            journal_totals_currency[jid] += payment.amount_currency
            if payment.currency_id.name == 'PYG':
                journal_totals_gs[jid] += payment.amount_local
            else:
                journal_totals_usd[jid] += payment.amount_currency

            total_local += payment.amount_local
            total_currency += payment.amount_currency
            if payment.currency_id and payment.currency_id.name == 'PYG':
                total_totales += payment.amount_local

        base_values.update({
            'docs': all_payments,
            'payments_grouped': payments_grouped,
            'journal_totals_currency': journal_totals_currency,
            'journal_totals_local': journal_totals_local,
            'journal_totals_gs': journal_totals_gs,
            'journal_totals_usd': journal_totals_usd,
            'total_local': total_local,
            'total_currency': total_currency,
            'total_totales': total_totales,
        })
        return base_values

    # Extiende la exportación a Excel para incluir pagos POS
    class DownloadXLS(http.Controller):
        @http.route('/getPaymentReport/<int:id>', auth='public')
        def generarXLSX(self, id=None, **kw):
            record = request.env['sati_payment_report.wizard'].browse(id)

            # Obtiene pagos de account.payment y agrega los de POS mediante concatenación de listas
            all_payments = list(record.get_payments())
            try:
                pos_payments = record.get_pos_payments()
                all_payments += list(pos_payments)
            except Exception:
                pass

            payments_grouped = {}
            journal_totals_local = {}
            journal_totals_currency = {}
            journal_totals_gs = {}
            journal_totals_usd = {}
            total_local = 0
            total_currency = 0
            total_totales = 0

            # Procesa los pagos combinados
            for payment in all_payments:
                if payment._name == 'pos.payment':
                    jid = payment.payment_method_id.journal_id.id
                else:
                    jid = payment.journal_id.id
                if jid not in payments_grouped:
                    payments_grouped[jid] = []
                    journal_totals_local[jid] = 0
                    journal_totals_currency[jid] = 0
                    journal_totals_gs[jid] = 0
                    journal_totals_usd[jid] = 0
                payments_grouped[jid].append(payment)
                journal_totals_local[jid] += payment.amount_local
                if payment.currency_id.name == 'PYG':
                    journal_totals_gs[jid] += payment.amount_local
                else:
                    journal_totals_usd[jid] += payment.amount_currency

            # Obtiene los diarios a partir de las claves de los totales
            journal_ids = request.env['account.journal'].browse(
                set(journal_totals_local.keys()).union(journal_totals_currency.keys())
            )

            i = 3  # Comienza en la fila 4
            fp = io.BytesIO()
            workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
            sheet = workbook.add_worksheet('Reporte de pagos')
            bold = workbook.add_format({'bold': True, 'fg_color': 'gray', 'align': 'center'})
            date_format = workbook.add_format({'num_format': 'dd-mm-yyyy'})
            merge_format = workbook.add_format({
                'bold': 1,
                'border': 1,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': 'gray'
            })
            sheet.set_column('A:E', 25)
            sheet.set_column('F:G', 35)

            # Escribe el título y rango de fechas
            sheet.merge_range('A1:G1', 'Reporte de pagos', merge_format)
            sheet.merge_range('A2:G2',
                              'Fecha Desde: ' + str(record.start_date) + ' - Fecha Hasta: ' + str(record.end_date),
                              merge_format)
            sheet.write(2, 0, 'Fecha', bold)
            sheet.write(2, 1, 'Diario', bold)
            sheet.write(2, 2, 'Cliente', bold)
            sheet.write(2, 3, 'Factura', bold)
            sheet.write(2, 4, 'Producto', bold)
            sheet.write(2, 5, 'Cantidad', bold)
            sheet.write(2, 6, 'Peso KG', bold)
            sheet.write(2, 7, 'Recibo', bold)
            sheet.write(2, 8, 'Cheque', bold)
            sheet.write(2, 9, 'Cheque Vencimiento', bold)
            sheet.write(2, 10, 'Moneda', bold)
            sheet.write(2, 11, 'Documento', bold)
            sheet.write(2, 12, 'Sucursal', bold)
            sheet.write(2, 13, 'Pago de Recibo', bold)
            sheet.write(2, 14, 'Monto Fac. s/ IVA', bold)
            sheet.write(2, 15, 'Monto Fac. Total', bold)
            sheet.write(2, 16, 'Monto moneda local', bold)
            sheet.write(2, 17, 'Monto moneda extranjera', bold)
            sheet.write(2, 18, 'Comercial', bold)
            sheet.write(2, 19, 'Tipo Factura', bold)
            sheet.write(2, 20, 'Categoria', bold)
            sheet.write(2, 21, 'Fecha Factura', bold)

            # Procesa cada diario y sus pagos
            for journal in journal_ids:
                sheet.write(i, 0, journal.name, bold)
                i += 1
                for p in sorted(payments_grouped[journal.id], key=lambda x: (x.report_date)):
                    if p._name == 'pos.payment':
                        date_val = p.payment_date
                        sheet.write(i, 0, date_val, date_format)
                        sheet.write(i, 1, p.payment_method_id.journal_id.name)
                        sheet.write(i, 2, p.partner_id.name)
                        # Se asume que la factura se obtiene desde el pedido de POS
                        sheet.write(i, 3, p.pos_order_id.account_move.nro_factura or '')
                        sheet.write(i, 10, p.currency_id.name)
                        sheet.write(i, 11, p.name)
                        sheet.write(i, 16, p.amount_local)
                        sheet.write(i, 7, p.pos_order_id.name)
                        if record.detallado and p.pos_order_id.account_move.invoice_line_ids:
                            for pro in p.pos_order_id.account_move.invoice_line_ids:
                                sheet.write(i, 4, pro.product_id.name)
                                sheet.write(i, 5, pro.quantity)
                                sheet.write(i, 6, pro.peso_kg)
                                sheet.write(i, 18, p.pos_order_id.account_move.invoice_user_id.name)
                                sheet.write(i, 21, p.pos_order_id.account_move.invoice_date, date_format)
                                sheet.write(i, 20, p.partner_id.category_id.name)
                                sheet.write(i, 19, 'Contado' if p.pos_order_id.account_move.tipo_factura == '1' else 'Crédito')
                                i += 1
                        i += 1
                    elif p._name == 'account.payment':
                        date_val = p.date
                        sheet.write(i, 21, p.recibo_id.fecha, date_format)
                        sheet.write(i, 1, p.journal_id.name)
                        sheet.write(i, 2, p.partner_id.name)
                        if p.reconciled_invoice_ids and not p.recibo_id:
                            for move in p.reconciled_invoice_ids:
                                sheet.write(i, 3, move.nro_factura)
                                i += 1
                                if record.detallado and move.invoice_line_ids:
                                    for line in move.invoice_line_ids:
                                        sheet.write(i, 4, line.product_id.name)
                                        sheet.write(i, 5, line.quantity)
                                        sheet.write(i, 6, line.peso_kg)
                                        sheet.write(i, 18, move.invoice_user_id.name)
                                        sheet.write(i, 3, move.invoice_date, date_format)
                                        sheet.write(i, 20, move.partner_id.category_id.name)
                                        sheet.write(i, 19, 'Contado' if move.tipo_factura == '1' else 'Crédito')
                                        i += 1
                        elif p.recibo_id:
                            sheet.write(i, 1, p.journal_id.name)
                            sheet.write(i, 2, p.partner_id.name)
                            sheet.write(i, 10, p.currency_id.name)
                            sheet.write(i, 11, p.name)
                            sheet.write(i, 12, p.cuenta_analitica.name)
                            sheet.write(i, 16, p.amount_local)
                            sheet.write(i, 7, p.recibo_id.name)
                            i += 1

                        if p.payment_type == 'inbound':
                            if p.recibo_id:
                                sheet.write(i, 0, p.recibo_id.fecha, date_format)
                            else:
                                sheet.write(i, 0, p.date, date_format)
                    total_local += p.amount_local
                    if p.currency_id and p.currency_id.name == 'PYG':
                        total_totales += p.amount_local
                i += 1

            # Sección de totales
            sheet.merge_range('A' + str(i + 1) + ':C' + str(i + 1), 'Totales por Diario', merge_format)
            i += 1
            sheet.write(i, 0, 'Diario', bold)
            sheet.write(i, 1, 'Total conversion moneda local', bold)
            sheet.write(i, 2, 'Total moneda extranjera', bold)
            sheet.write(i, 3, 'Total moneda local', bold)
            i += 1
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
            return request.make_response(
                fp.read(),
                [('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                 ('Content-Disposition', content_disposition('reporte_pagos.xlsx'))]
            )

class PosPayment(models.Model):
    _inherit = "pos.payment"

    invoice_number = fields.Char(string="Número de Factura", compute="_compute_invoice_number", store=True)

    def _compute_invoice_number(self):
        for payment in self:
            if hasattr(payment, 'pos_order_id') and payment.pos_order_id and payment.pos_order_id.account_move:
                payment.invoice_number = payment.pos_order_id.account_move.nro_factura
            else:
                payment.invoice_number = False
