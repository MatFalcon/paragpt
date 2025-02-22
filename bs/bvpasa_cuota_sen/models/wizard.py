# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT


class WizardReporteCuotaSen(models.TransientModel):
    _name = 'wizard_reporte_cuota_sen'
    _description = 'Wizard Reporte de Cuota SEN'

    year = fields.Integer(string="Año", required=True)

    def print_report_xlsx(self):
        data = {
            'year': self.year
        }
        return self.env.ref('bvpasa_cuota_sen.report_action').report_action(self, data=data)


class ReporteCuotaSen(models.AbstractModel):
    _name = 'report.bvpasa_cuota_sen.reporte_cuota_sen_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_first_date_of_month(self, year, month):
        first_date = datetime(year, month, 1)
        return first_date.date()

    def get_last_date_of_month(self, year, month):
        if month == 12:
            last_date = datetime(year, month, 31)
        else:
            last_date = datetime(year, month + 1, 1) + timedelta(days=-1)
        return last_date.date()

    def generate_xlsx_report(self, workbook, data, datas):
        year = int(data['year'])

        global sheet
        global bold
        global num_format
        global position_x
        global position_y
        sheet = workbook.add_worksheet('OP Saldos')
        cell_format = workbook.add_format({'font_name': 'Roboto'})
        bold = workbook.add_format({'bold': True, 'font_name': 'Roboto'})
        subtitulo = workbook.add_format(
            {'color': '#ffffff', 'bold': True, 'bg_color': '#501e53', 'font_name': 'Roboto'})
        subtitulo_amarillo = workbook.add_format(
            {'color': '#ffffff', 'bold': True, 'bg_color': '#fbba00', 'font_name': 'Roboto'})
        titulo = workbook.add_format({'color': '#000000', 'bold': True, 'bg_color': '#f2f2f2', 'font_name': 'Roboto'})
        numerico = workbook.add_format({'num_format': True, 'align': 'right', 'font_name': 'Roboto'})
        numerico.set_num_format('#,##0')
        numerico_total = workbook.add_format(
            {'num_format': True, 'align': 'right', 'bold': True, 'font_name': 'Roboto'})

        usd_format = workbook.add_format({'num_format': '$#,##0.00', 'align': 'right', 'font_name': 'Roboto'})

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

        simpleWrite("Año", bold)
        rightAndWrite(year, cell_format)

        breakAndWrite('Facturaciones y saldos', bold)
        addRight()
        addRight()
        x = 0
        company = self.env.company
        while x <= 12:
            addRight()
            addRight()
            addRight()
            addRight()
            if x%2 == 0:
                rightAndWrite("TC", subtitulo_amarillo)
            else:
                rightAndWrite("TC", subtitulo)
            x = x + 1

        addSalto()
        rightAndWrite("40%", titulo)
        rightAndWrite("60%", titulo)

        x = 1
        sum_rate = 0
        while x <= 12:
            _get_conversion_rate = company.secondary_currency_id._get_conversion_rate_tipo_cambio_comprador
            currency_rate = _get_conversion_rate(
                company.secondary_currency_id,
                company.currency_id,
                company,
                datetime(year, x, 25)
            )
            addRight()
            addRight()
            addRight()
            addRight()
            rightAndWrite(currency_rate, numerico)
            x = x+1
            sum_rate = currency_rate + sum_rate

        addRight()
        addRight()
        addRight()
        addRight()
        rightAndWrite(sum_rate/12, numerico)

        breakAndWrite('Aranceles por operaciones', subtitulo)
        rightAndWrite("Cuota SEN", subtitulo)
        rightAndWrite("Saldo a favor", subtitulo)
        rightAndWrite("Pago Anual USD", subtitulo)
        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        x = 0
        for mes in meses:
            if x % 2 == 0:
                formato = subtitulo_amarillo
            else:
                formato = subtitulo
            rightAndWrite("Arancel PYG %s" % mes, formato)
            rightAndWrite("Arancel USD %s" % mes, formato)
            rightAndWrite("Total %s Guaranizado" % mes, formato)
            rightAndWrite("Total %s Dolarizado" % mes, formato)
            rightAndWrite("Saldo %s" % mes, formato)
            x = x+1
        rightAndWrite("Total anual Arancel PYG", subtitulo)
        rightAndWrite("Total anual Arancel USD", subtitulo)
        rightAndWrite("Total anual de Aranceles Guaranizados", subtitulo_amarillo)
        rightAndWrite("Total anual de Aranceles Dolarizados", subtitulo_amarillo)


        registros = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search([('active', '=', True),
                                                                            ('nc_fecha', '>=',self.get_first_date_of_month(year,1)),
                                                                            ('nc_fecha', '<=',
                                                                             self.get_last_date_of_month(year,12))])
        product_servicio_sen_id = self.env['ir.config_parameter'].sudo().get_param(
            'product_servicio_sen_id')
        product_ingresos_anticipados_id = self.env['ir.config_parameter'].sudo().get_param(
            'product_ingresos_anticipados_id')

        partners = set(registros.mapped('partner_id'))
        sum_saldo_favor =0
        sum_cuota_sen = 0
        sum_total = 0
        for p in partners:
            factura_cuota_sen = registros.mapped('factura_cuota_sen_id')[0]
            saldo_favor = sum(factura_cuota_sen.mapped('invoice_line_ids').filtered(
                lambda x: x.product_id.id == int(product_ingresos_anticipados_id)).mapped('price_total'))
            cuota_sen = sum(factura_cuota_sen.mapped('invoice_line_ids').filtered(
                lambda x: x.product_id.id == int(product_servicio_sen_id)).mapped('price_total'))
            sum_saldo_favor = sum_saldo_favor + saldo_favor
            sum_total = sum_total + factura_cuota_sen.amount_total
            sum_cuota_sen = sum_cuota_sen + cuota_sen
            breakAndWrite(p.name, cell_format)
            rightAndWrite(cuota_sen, usd_format)
            rightAndWrite(saldo_favor, usd_format)
            rightAndWrite(factura_cuota_sen.amount_total, usd_format)
            m = 1
            saldo_mes = saldo_favor
            pyg_sum = 0
            usd_sum = 0
            total_pyg = 0
            total_usd = 0
            while m <= 12:
                r_mes = registros.filtered(lambda x: x.partner_id == p
                                                     and self.get_first_date_of_month(year,m) <= x.nc_fecha <= self.get_last_date_of_month(year, m))
                pyg_mes = sum(r_mes.filtered(lambda x:x.nota_credito_id.currency_id.name == 'PYG').mapped('nota_credito_id.amount_total'))
                pyg_sum = pyg_sum + pyg_mes
                rightAndWrite(pyg_mes, numerico)
                usd_mes = sum(r_mes.filtered(lambda x:x.nota_credito_id.currency_id.name == 'USD').mapped('nota_credito_id.amount_total'))
                usd_sum = usd_sum + usd_mes
                rightAndWrite(usd_mes, usd_format)
                _get_conversion_rate = company.secondary_currency_id._get_conversion_rate_tipo_cambio_comprador
                currency_rate = _get_conversion_rate(
                    company.secondary_currency_id,
                    company.currency_id,
                    company,
                    datetime(year, m, 25)
                )
                total_pyg_mes = (usd_mes*currency_rate) + pyg_mes
                total_pyg = total_pyg_mes + total_pyg
                rightAndWrite(total_pyg_mes, numerico)
                total_usd_mes = (pyg_mes/currency_rate) + usd_mes
                total_usd = total_usd + total_usd_mes
                rightAndWrite(total_usd_mes, usd_format)
                saldo_mes = saldo_mes - total_usd_mes
                rightAndWrite(saldo_mes, usd_format)
                m = m+1

            rightAndWrite(pyg_sum, numerico)
            rightAndWrite(usd_sum, usd_format)
            rightAndWrite(total_pyg, numerico)
            rightAndWrite(total_usd, usd_format)

        breakAndWrite('TOTALES', titulo)
        rightAndWrite(sum_cuota_sen, usd_format)
        rightAndWrite(sum_saldo_favor,usd_format)
        rightAndWrite(sum_total,usd_format)
        m = 1
        pyg_sum_final = 0
        usd_sum_final = 0
        total_pyg_final = 0
        total_usd_final = 0
        saldo_mes = sum_saldo_favor
        while m <= 12:
            r_mes = registros.filtered(lambda x: self.get_first_date_of_month(year,m) <= x.nc_fecha <= self.get_last_date_of_month(year, m))
            pyg_mes = sum(r_mes.filtered(lambda x: x.nota_credito_id.currency_id.name == 'PYG').mapped('nota_credito_id.amount_total'))
            pyg_sum_final += pyg_mes
            rightAndWrite(pyg_mes, numerico)
            usd_mes = sum(r_mes.filtered(lambda x: x.nota_credito_id.currency_id.name == 'USD').mapped('nota_credito_id.amount_total'))
            usd_sum_final += usd_mes
            rightAndWrite(usd_mes, usd_format)
            _get_conversion_rate = company.secondary_currency_id._get_conversion_rate_tipo_cambio_comprador
            currency_rate = _get_conversion_rate(
                company.secondary_currency_id,
                company.currency_id,
                company,
                datetime(year, m, 25)
            )
            total_pyg_mes = (usd_mes * currency_rate) + pyg_mes
            total_pyg_final = total_pyg_final + total_pyg_mes
            rightAndWrite(total_pyg_mes, numerico)
            total_usd_mes = (pyg_mes / currency_rate) + usd_mes
            total_usd_final = total_usd_final + total_usd_mes
            rightAndWrite(total_usd_mes, usd_format)
            saldo_mes = saldo_mes - total_usd_mes
            rightAndWrite(saldo_mes, usd_format)
            m = m + 1

        rightAndWrite(pyg_sum_final, numerico)
        rightAndWrite(usd_sum_final, usd_format)
        rightAndWrite(total_pyg_final, numerico)
        rightAndWrite(total_usd_final, usd_format)



