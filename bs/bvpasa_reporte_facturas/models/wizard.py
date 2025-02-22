# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class WizardReporteFacturas(models.TransientModel):
    _name = 'wizard_reporte_facturas'
    _description = 'Wizard Reporte de Facturas'

    fecha_inicio = fields.Date(string="Fecha Inicial", default=fields.Date.today(), required=True)
    fecha_fin = fields.Date(string="Fecha Final", default=fields.Date.today(), required=True)
    payment_state = fields.Selection(
        selection=[
            ('not_paid', 'No pagadas'),
            ('in_payment', 'En proceso de pago'),
            ('paid', 'Pagado'),
            ('partial', 'Pagado Parcialmente'),
            ('reversed', 'Revertido'),
            ('invoicing_legacy', 'Factura Sistema Anterior'),
        ], required=False, string="Estado de Pago"
    )

    def print_report_xlsx(self):
        data = {
            'fecha_inicio': self.fecha_inicio,
            'fecha_fin': self.fecha_fin,
            'payment_state': self.payment_state if self.payment_state else False

        }
        return self.env.ref('bvpasa_reporte_facturas.report_action').report_action(self, data=data)


class ReporteFacturas(models.AbstractModel):
    _name = 'report.bvpasa_reporte_facturas.reporte_facturas_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, datas):
        date_start = data['fecha_inicio']
        date_end = data['fecha_fin']
        date_start_obj = datetime.strptime(date_start, DATE_FORMAT)
        date_end_obj = datetime.strptime(date_end, DATE_FORMAT)

        search_domain = [('move_type', 'in', ['out_invoice', 'in_invoice']),
                         ('state', '!=', 'draft'),
                         ('date', '>=', date_start_obj.strftime(DATETIME_FORMAT)),
                         ('date', '<=', date_end_obj.strftime(DATETIME_FORMAT))]

        if data['payment_state']:
            search_domain = search_domain + [('payment_state', '=', data['payment_state'])]

        facturas = self.env['account.move'].search(search_domain)

        global sheet
        global bold
        global num_format
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Emitidas')
        cell_format = workbook.add_format({'font_name':'Roboto'})
        bold = workbook.add_format({'bold': True,'font_name':'Roboto'})
        subtitulo = workbook.add_format({'color': '#ffffff','bold':True,'bg_color':'#501e53','font_name':'Roboto'})
        titulo = workbook.add_format({'color': '#000000','bold':True,'bg_color':'#bfbfbf', 'font_name':'Roboto'})
        numerico = workbook.add_format({'num_format': True, 'align': 'right', 'font_name':'Roboto'})
        numerico.set_num_format('#,##0')
        numerico_total = workbook.add_format(
            {'num_format': True, 'align': 'right', 'bold': True, 'font_name':'Roboto'})

        usd_format = workbook.add_format({'num_format': '$#,##0.00', 'align':'right', 'font_name':'Roboto'})

        numerico_total.set_num_format('#,##0')
        wrapped_text = workbook.add_format()
        wrapped_text.set_text_wrap()
        wrapped_text_bold = workbook.add_format({'bold': True})
        wrapped_text_bold.set_text_wrap()

        position_x = 0
        position_y = 0

        def addSalto():
            global position_x
            global position_y
            position_x = 0
            position_y += 1

        def addRight():
            global position_x
            position_x += 1

        def breakAndWrite(to_write, format=None):
            global sheet
            addSalto()
            sheet.write(position_y, position_x, to_write, format)

        def simpleWrite(to_write, format=None):
            global sheet
            sheet.write(position_y, position_x, to_write, format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            sheet.write(position_y, position_x, to_write, format)

        simpleWrite("Fecha Inicio",bold)
        rightAndWrite(date_start_obj.strftime("%d/%m/%Y"))
        rightAndWrite("Fecha Fin",bold)
        rightAndWrite(date_end_obj.strftime("%d/%m/%Y"))

        def printCabecera(title=None):
            breakAndWrite(title, titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)
            rightAndWrite("", titulo)

            breakAndWrite("Entidad", subtitulo)
            rightAndWrite("Nacionalidad", subtitulo)
            rightAndWrite("Factura", subtitulo)
            rightAndWrite("Cuenta Contable", subtitulo)
            rightAndWrite("Denominación de la cuenta", subtitulo)
            rightAndWrite("Cuenta Analitca", subtitulo)
            rightAndWrite("Concepto de la Factura", subtitulo)
            rightAndWrite("Fecha de Factura", subtitulo)
            rightAndWrite("Fecha de Vencimiento", subtitulo)
            rightAndWrite("Moneda", subtitulo)
            rightAndWrite("Importe en moneda original", subtitulo)
            rightAndWrite("Importe en moneda local", subtitulo)
            rightAndWrite("Tipo de Cambio", subtitulo)
            rightAndWrite("Cobros", subtitulo)
            rightAndWrite("Saldo", subtitulo)
            rightAndWrite("Estado de Pago", subtitulo)
            rightAndWrite("Fechas de Pago", subtitulo)
            rightAndWrite("Estado de Factura", subtitulo)

        def printData(l=None):
            pagos = self.env['account.payment'].search([('state','=','posted')])
            if l.move_id.move_type == 'out_invoice':
                pagos = pagos.filtered(lambda x:l.move_id.id in x.reconciled_invoice_ids.ids)
            if l.move_id.move_type == 'in_invoice':
                pagos = pagos.filtered(lambda x:l.move_id.id in x.reconciled_bill_ids.ids)
            text = ''
            breakAndWrite(l.partner_id.name, cell_format)
            if l.move_id.res90_tipo_identificacion == '14':
                rightAndWrite('Extranjero', cell_format)
            else:
                rightAndWrite('Local', cell_format)
            rightAndWrite(l.move_id.name, cell_format)
            rightAndWrite(l.account_id.code, cell_format)
            rightAndWrite(l.account_id.name, cell_format)
            rightAndWrite(l.analytic_account_id.name if l.analytic_account_id else "", cell_format)
            rightAndWrite(l.name, cell_format)
            rightAndWrite(l.date.strftime("%d/%m/%Y"), cell_format)
            rightAndWrite(l.move_id.invoice_date_due.strftime("%d/%m/%Y"), cell_format)
            rightAndWrite(l.currency_id.name, cell_format)
            rightAndWrite(l.price_total, numerico)
            rightAndWrite(l.price_total * l.move_id.currency_rate, numerico)
            rightAndWrite(l.move_id.currency_rate, numerico)
            if l.move_id.payment_state == 'not_paid':
                rightAndWrite(0, cell_format)
                rightAndWrite(l.price_total, numerico)
                rightAndWrite("No pagadas", cell_format)
            elif l.move_id.payment_state == 'in_payment':
                rightAndWrite(0, cell_format)
                rightAndWrite(l.price_total, numerico)
                rightAndWrite("En proceso de pago", cell_format)
            elif l.move_id.payment_state == 'paid':
                rightAndWrite(l.price_total, numerico)
                rightAndWrite(0, cell_format)
                rightAndWrite("Pagado", cell_format)
            elif l.move_id.payment_state == 'partial':
                pagado = (l.move_id.amount_total - l.move_id.amount_residual)
                por_pag = pagado * 100 / l.move_id.amount_total
                monto_pag_l = (por_pag * l.price_total) / 100
                rightAndWrite(monto_pag_l, numerico)
                rightAndWrite(l.price_total - monto_pag_l, numerico)
                rightAndWrite("Pagado parcialmente", cell_format)
            elif l.move_id.payment_state == 'reversed':
                rightAndWrite(l.price_total, numerico)
                rightAndWrite(0, cell_format)
                rightAndWrite("Revertido", cell_format)
            if pagos:
                for p in pagos:
                    text = text + p.date.strftime("%d/%m/%Y") + ' '
            else:
                for partial, amount, counterpart_line in l.move_id._get_reconciled_invoices_partials():
                    text = text + counterpart_line.date.strftime("%d/%m/%Y") + ' '
            rightAndWrite(text, cell_format)
            if l.move_id.state == 'posted':
                rightAndWrite("Publicado", cell_format)
            elif l.move_id.state == 'cancel':
                rightAndWrite("Cancelado", cell_format)

        printCabecera(title="FACTURAS EMITIDAS")

        importe_moneda_local = 0
        for l in facturas.filtered(lambda x: x.move_type == 'out_invoice').mapped('invoice_line_ids'):
            printData(l)
            importe_moneda_local = importe_moneda_local + l.price_total * l.move_id.currency_rate


        saldo_usd = sum(facturas.filtered(lambda x: x.move_type == 'out_invoice' and x.currency_id.name == "USD").mapped('amount_residual'))
        importe_usd = sum(facturas.filtered(lambda x: x.move_type == 'out_invoice' and x.currency_id.name == "USD").mapped('amount_total'))
        cobro_usd = importe_usd - saldo_usd
        saldo_gs = sum(facturas.filtered(lambda x: x.move_type == 'out_invoice' and x.currency_id.name == "PYG").mapped('amount_residual'))
        importe_gs = sum(facturas.filtered(lambda x: x.move_type == 'out_invoice' and x.currency_id.name == "PYG").mapped('amount_total'))
        cobro_gs = importe_gs - saldo_gs

        addSalto()
        breakAndWrite("Total USD", bold)
        rightAndWrite(importe_usd, usd_format)

        breakAndWrite("Total PYG", bold)
        rightAndWrite(importe_gs, numerico)

        breakAndWrite("Importe en moneda local", bold)
        rightAndWrite(importe_moneda_local, numerico)

        breakAndWrite("Cobros USD", bold)
        rightAndWrite(cobro_usd, usd_format)

        breakAndWrite("Cobros PYG", bold)
        rightAndWrite(cobro_gs, numerico)

        breakAndWrite("Saldo USD", bold)
        rightAndWrite(saldo_usd, usd_format)

        breakAndWrite("Saldo PYG", bold)
        rightAndWrite(saldo_gs, numerico)

        sheet = workbook.add_worksheet('Recibidas')
        position_x = 0
        position_y = 0
        simpleWrite("Fecha Inicio", bold)
        rightAndWrite(date_start_obj.strftime("%d/%m/%Y"))
        rightAndWrite("Fecha Fin", bold)
        rightAndWrite(date_end_obj.strftime("%d/%m/%Y"))
        printCabecera(title="FACTURAS RECIBIDAS")
        importe_moneda_local = 0
        for l in facturas.filtered(lambda x: x.move_type == 'in_invoice').mapped('invoice_line_ids'):
            printData(l)
            importe_moneda_local = importe_moneda_local + l.price_total * l.move_id.currency_rate


        saldo_usd = sum(
            facturas.filtered(lambda x: x.move_type == 'in_invoice' and x.currency_id.name == "USD").mapped(
                'amount_residual'))
        importe_usd = sum(
            facturas.filtered(lambda x: x.move_type == 'in_invoice' and x.currency_id.name == "USD").mapped(
                'amount_total'))
        cobro_usd = importe_usd - saldo_usd
        saldo_gs = sum(
            facturas.filtered(lambda x: x.move_type == 'in_invoice' and x.currency_id.name == "PYG").mapped(
                'amount_residual'))
        importe_gs = sum(
            facturas.filtered(lambda x: x.move_type == 'in_invoice' and x.currency_id.name == "PYG").mapped(
                'amount_total'))
        cobro_gs = importe_gs - saldo_gs

        addSalto()
        breakAndWrite("Total USD", bold)
        rightAndWrite(importe_usd, usd_format)

        breakAndWrite("Total PYG", bold)
        rightAndWrite(importe_gs, numerico)

        breakAndWrite("Importe en moneda local", bold)
        rightAndWrite(importe_moneda_local, numerico)

        breakAndWrite("Cobros USD", bold)
        rightAndWrite(cobro_usd, usd_format)

        breakAndWrite("Cobros PYG", bold)
        rightAndWrite(cobro_gs, numerico)

        breakAndWrite("Saldo USD", bold)
        rightAndWrite(saldo_usd, usd_format)

        breakAndWrite("Saldo PYG", bold)
        rightAndWrite(saldo_gs, numerico)
