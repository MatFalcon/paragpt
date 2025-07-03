# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)


class WizardReporteVolumenNegociado(models.TransientModel):
    _name = 'wizard_reporte_volumen_negociado'
    _description = 'Wizard Reporte de Volumen Negociado'

    year = fields.Integer(string="Año", required=True)

    def print_report_xlsx(self):
        data = {
            'year': self.year
        }
        return self.env.ref('pbp.report_action_volumen_negociado').report_action(self, data=data)


class ReportevolumenNegociado(models.AbstractModel):
    _name = 'report.pbp.reporte_volumen_negociado_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_currency_rate(self,day):
        # Buscar la moneda 'USD-COMPRA'
        usd_currency = self.env['res.currency'].search([('name', '=', 'USD-Compra')], limit=1)

        # Buscar la tasa de cambio en res.currency.rate para la fecha last_day_month
        currency_rate = self.env['res.currency.rate'].search([
            ('currency_id', '=', usd_currency.id),
            ('name', '=', day)
        ], limit=1).set_venta  # Extrae el valor del campo set_venta
        # Si no se encuentra, establecer un valor por defecto o lanzar una advertencia
        if not currency_rate:
            currency_rate = 1  # Puedes definir otro valor por defecto si es necesario
            _logger.warning(f"No se encontró tasa de cambio para USD-COMPRA el {day}")
        return currency_rate

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
        sheet = workbook.add_worksheet('Tabla')
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

        simpleWrite("Año " + str(year), bold)
        x = 0
        company = self.env.company
        while x < 12:
            if x % 2 == 0:
                rightAndWrite("TC", subtitulo_amarillo)
            else:
                rightAndWrite("TC", subtitulo)
            x = x + 1

        addSalto()

        x = 1
        sum_rate = 0
        while x <= 12:
            currency_rate = self.get_currency_rate(self.get_last_date_of_month(year, x))
            _logger.info(f"Tipo de cambio para {self.get_last_date_of_month(year, x)}: {currency_rate}")  
            rightAndWrite(currency_rate, numerico)  
            x = x + 1
            sum_rate = currency_rate + sum_rate

        meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
        x = 0
        addSalto()

        for mes in meses:
            if x % 2 == 0:
                formato = subtitulo_amarillo
            else:
                formato = subtitulo
            rightAndWrite(mes, formato)
            x = x + 1

        breakAndWrite('Acciones desmaterializadas', subtitulo)
        breakAndWrite("Bonos", subtitulo)
        breakAndWrite("Fondos de Inversión", subtitulo)
        breakAndWrite("Negociabilidad", subtitulo)
        breakAndWrite("Repos", subtitulo)
        breakAndWrite("Total General", titulo)
        breakAndWrite("Acciones físicas", subtitulo)
        breakAndWrite("Custodia Física", subtitulo)
        breakAndWrite("Futuro", subtitulo)
        breakAndWrite("Total", titulo)

        novedades = self.env['pbp.novedades'].search([('instrumento', '!=', False),
                                                      ('tipo_operacion','in',['Reportado','Venta']),
                                                      ('fecha_operacion', '>=', self.get_first_date_of_month(year, 1)),
                                                      ('fecha_operacion', '<=',
                                                       self.get_last_date_of_month(year, 12))])

        sistema_tradicional = self.env['pbp.novedades_series'].search([
            ('fecha', '>=', self.get_first_date_of_month(year, 1)),
            ('fecha', '<=',
             self.get_last_date_of_month(year, 12))])

        custodia_fisica = self.env['custodia_fisica.custodia_fisica'].search([
            ('fecha_inicio', '>=', self.get_first_date_of_month(year, 1)),
            ('fecha_inicio', '<=',
             self.get_last_date_of_month(year, 12)),
            ('invoice_id', '!=', False)])

        futuro = self.env['pbp.operacion_futuro'].search([
            ('fecha', '>=', self.get_first_date_of_month(year, 1)),
            ('fecha', '<=',
             self.get_last_date_of_month(year, 12))])

        m = 1
        addSalto()
        while m <= 12:
            position_y = 3
            last_day_month = self.get_last_date_of_month(year, m)
            novedades_mes = novedades.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha_operacion <= last_day_month)
            repos_pyg = novedades_mes.filtered(lambda x: x.mercado == 'Repos' and x.currency_id.name == "PYG")
            repos_usd = novedades_mes.filtered(lambda x: x.mercado == 'Repos' and x.currency_id.name == "USD-Compra")
            fondos_pyg = novedades_mes.filtered(
                lambda x: x.instrumento == 'Fondos de Inversión' and x.currency_id.name == "PYG")
            fondos_usd = novedades_mes.filtered(
                lambda x: x.instrumento == 'Fondos de Inversión' and x.currency_id.name == "USD-Compra")
            acciones_pyg = novedades_mes.filtered(lambda x: x.instrumento == 'Acciones' and x.currency_id.name == "PYG")
            acciones_usd = novedades_mes.filtered(lambda x: x.instrumento == 'Acciones' and x.currency_id.name == "USD-Compra")
            bonos_pyg = novedades_mes.filtered(
                lambda x: ('bono' in x.instrumento.lower() or 'bbcp' in x.instrumento.lower())
                          and x.currency_id.name == "PYG")
            bonos_usd = novedades_mes.filtered(
                lambda x: 'bono' in x.instrumento.lower() and x.currency_id.name == "USD-Compra")
            #print("BONOS USD", bonos_usd)
            negociabilidad_usd = novedades_mes.filtered(lambda x: ('bono' in x.instrumento.lower() or 'bbcp' in x.instrumento.lower())
                                                                  and x.partner_id.entidad_publica
                                                                  and x.currency_id.name == "USD-Compra")
            negociabilidad_pyg = novedades_mes.filtered(lambda x: ('bono' in x.instrumento.lower() or 'bbcp' in x.instrumento.lower())
                                                                  and x.partner_id.entidad_publica
                                                                  and x.currency_id.name == "PYG")
            futuro_usd = futuro.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha <= last_day_month)

            # Calcular cantidades y almacenarlas en variables
            # acciones_cantidad = sum(acciones_pyg.mapped('cantidad')) + sum(acciones_usd.mapped('cantidad'))
            # bonos_cantidad = sum(bonos_pyg.mapped('cantidad')) + sum(bonos_usd.mapped('cantidad'))
            # fondos_cantidad = sum(fondos_pyg.mapped('cantidad')) + sum(fondos_usd.mapped('cantidad'))
            # negociabilidad_cantidad = sum(negociabilidad_pyg.mapped('cantidad')) + sum(negociabilidad_usd.mapped('cantidad'))
            # repos_cantidad = sum(repos_pyg.mapped('cantidad')) + sum(repos_usd.mapped('cantidad'))
            # print("ACCIONES", acciones_cantidad)
            # print("BONOS", bonos_cantidad)
            # print("FONDOS", fondos_cantidad)
            # print("REPOS", repos_cantidad)
            sistema_tradicional_mes = sistema_tradicional.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha <= last_day_month)
            # acciones_fisicas_cantidad = sum(sistema_tradicional_mes.mapped('cantidad'))
            # print("ACCIONES FISICAS", acciones_cantidad)
            custodia_fisica_mes = custodia_fisica.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha_inicio <= last_day_month)
            # custodia_fisica_cantidad = sum(custodia_fisica_mes.mapped('line_ids').mapped('cantidad'))
            # print("CUSTODIAS", custodia_fisica_cantidad)
            # futuro_cantidad = sum(futuro_usd.mapped('cantidad'))

            # sum1_cantidad = acciones_cantidad + bonos_cantidad + fondos_cantidad + negociabilidad_cantidad + repos_cantidad
            # sum2_cantidad = sum1_cantidad + acciones_fisicas_cantidad + custodia_fisica_cantidad + futuro_cantidad

            repos_mes = (sum(repos_pyg.mapped('volumen_gs')) + sum(repos_usd.mapped('volumen_gs_usd'))) / currency_rate
            fondos_mes = (sum(fondos_pyg.mapped('volumen_gs')) + sum(
                fondos_usd.mapped('volumen_gs_usd'))) / currency_rate
            acciones_mes = (sum(acciones_pyg.mapped('volumen_gs')) + sum(
                acciones_usd.mapped('volumen_gs_usd'))) / currency_rate
            bonos_mes = (sum(bonos_pyg.mapped('volumen_gs')) + sum(bonos_usd.mapped('volumen_gs_usd'))) / currency_rate
            negociabilidad_mes = (sum(negociabilidad_pyg.mapped('volumen_gs')) + sum(
                negociabilidad_usd.mapped('volumen_gs_usd'))) / currency_rate

            sistema_tradicional_mes = sistema_tradicional.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha <= last_day_month)

            custodia_fisica_pyg = sum(
                custodia_fisica_mes.mapped('line_ids').filtered(lambda x: x.currency_id.name == "PYG").mapped(
                    'valor_nominal'))
            custodia_fisica_usd = sum(
                custodia_fisica_mes.mapped('line_ids').filtered(lambda x: x.currency_id.name == "USD-Compra").mapped(
                    'valor_nominal'))

            futuro_mes = sum(futuro_usd.mapped('importe'))

            acciones_fisicas = sum(sistema_tradicional_mes.mapped('total')) / currency_rate

            custodia_fisica_total = custodia_fisica_usd + (custodia_fisica_pyg / currency_rate)

            position_x = m
            simpleWrite(acciones_mes, numerico)
            position_x = m
            position_y = position_y + 1
            simpleWrite(bonos_mes, numerico)
            position_x = m
            position_y = position_y + 1
            simpleWrite(fondos_mes, numerico)
            position_x = m
            position_y = position_y + 1
            simpleWrite(negociabilidad_mes, numerico)
            position_x = m
            position_y = position_y + 1
            simpleWrite(repos_mes, numerico)
            position_x = m
            position_y = position_y + 1
            sum1 = acciones_mes + bonos_mes + fondos_mes + negociabilidad_mes + repos_mes
            simpleWrite(sum1, numerico)
            position_x = m
            position_y = position_y + 1
            simpleWrite(acciones_fisicas, numerico)
            position_x = m
            position_y = position_y + 1
            simpleWrite(custodia_fisica_total, numerico)
            position_x = m
            position_y = position_y + 1
            simpleWrite(futuro_mes, numerico)
            position_x = m
            position_y = position_y + 1
            sum2 = sum1 + acciones_fisicas + custodia_fisica_total + futuro_mes
            simpleWrite(sum2, numerico)
            m = m + 1


        # ================================================
        # TABLA DE CANTIDADES SEPARADAS POR MONEDA
        # ================================================
        
        # Espacio entre tablas
        position_y += 3
        position_x = 0
        m = 1
        simpleWrite("Año " + str(year) + " - Cantidades por Moneda", bold)
        
        # Encabezados de meses duplicados (PYG y USD)
        x = 0
        for mes in meses:
            if x % 2 == 0:
                formato = subtitulo_amarillo
            else:
                formato = subtitulo
            # Columna PYG
            rightAndWrite(mes + " (PYG)", formato)
            # Columna USD
            rightAndWrite(mes + " (USD)", formato)
            x = x + 1

        # Mismos títulos de filas
        breakAndWrite('Acciones desmaterializadas', subtitulo)
        breakAndWrite("Bonos", subtitulo)
        breakAndWrite("Fondos de Inversión", subtitulo)
        breakAndWrite("Negociabilidad", subtitulo)
        breakAndWrite("Repos", subtitulo)
        breakAndWrite("Total General", titulo)
        breakAndWrite("Acciones físicas", subtitulo)
        breakAndWrite("Custodia Física", subtitulo)
        breakAndWrite("Futuro", subtitulo)
        breakAndWrite("Total", titulo)

        # Bucle principal modificado para dos columnas por mes
        addSalto()
        while m <= 12:
            position_y = position_y - 10  # Mismo ajuste de posición
            last_day_month = self.get_last_date_of_month(year, m)
            
            # Filtros (igual que antes)
            novedades_mes = novedades.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha_operacion <= last_day_month)
            repos_pyg = novedades_mes.filtered(lambda x: x.mercado == 'Repos' and x.currency_id.name == "PYG")
            repos_usd = novedades_mes.filtered(lambda x: x.mercado == 'Repos' and x.currency_id.name == "USD-Compra")
            fondos_pyg = novedades_mes.filtered(
                lambda x: x.instrumento == 'Fondos de Inversión' and x.currency_id.name == "PYG")
            fondos_usd = novedades_mes.filtered(
                lambda x: x.instrumento == 'Fondos de Inversión' and x.currency_id.name == "USD-Compra")
            acciones_pyg = novedades_mes.filtered(lambda x: x.instrumento == 'Acciones' and x.currency_id.name == "PYG")
            acciones_usd = novedades_mes.filtered(lambda x: x.instrumento == 'Acciones' and x.currency_id.name == "USD-Compra")
            bonos_pyg = novedades_mes.filtered(
                lambda x: ('bono' in x.instrumento.lower() or 'bbcp' in x.instrumento.lower())
                          and x.currency_id.name == "PYG")
            bonos_usd = novedades_mes.filtered(
                lambda x: 'bono' in x.instrumento.lower() and x.currency_id.name == "USD-Compra")
            negociabilidad_pyg = novedades_mes.filtered(lambda x: ('bono' in x.instrumento.lower() or 'bbcp' in x.instrumento.lower())
                                                                  and x.partner_id.entidad_publica
                                                                  and x.currency_id.name == "PYG")
            
            sistema_tradicional_mes = sistema_tradicional.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha <= last_day_month)
            
            custodia_fisica_mes = custodia_fisica.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha_inicio <= last_day_month)
            
            futuro_usd = futuro.filtered(
                lambda x: self.get_first_date_of_month(year, m) <= x.fecha <= last_day_month)

            # CALCULAR CANTIDADES POR MONEDA (sin sumar)
            # Acciones
            acciones_pyg_cant = sum(acciones_pyg.mapped('cantidad'))
            acciones_usd_cant = sum(acciones_usd.mapped('cantidad'))
            
            # Bonos
            bonos_pyg_cant = sum(bonos_pyg.mapped('cantidad'))
            bonos_usd_cant = sum(bonos_usd.mapped('cantidad'))
            
            # Fondos
            fondos_pyg_cant = sum(fondos_pyg.mapped('cantidad'))
            fondos_usd_cant = sum(fondos_usd.mapped('cantidad'))
            
            # Negociabilidad (solo PYG según tu filtro)
            negociabilidad_pyg_cant = sum(negociabilidad_pyg.mapped('cantidad'))
            
            # Repos
            repos_pyg_cant = sum(repos_pyg.mapped('cantidad'))
            repos_usd_cant = sum(repos_usd.mapped('cantidad'))
            
            # Acciones físicas (sistema tradicional)
            acciones_fisicas_pyg_cant = sum(sistema_tradicional_mes.mapped('cantidad'))
            
            # Custodia física
            custodia_pyg_cant = sum(custodia_fisica_mes.mapped('line_ids').filtered(
                lambda x: x.currency_id.name == "PYG").mapped('cantidad'))
            custodia_usd_cant = sum(custodia_fisica_mes.mapped('line_ids').filtered(
                lambda x: x.currency_id.name == "USD").mapped('cantidad'))
            
            # Futuro (solo USD según tu filtro)
            futuro_usd_cant = sum(futuro_usd.mapped('cantidad'))

            # ESCRITURA EN EXCEL (2 columnas por mes)
            col_pyg = (m * 2) - 1  # Columna impar (1, 3, 5...)
            col_usd = m * 2         # Columna par (2, 4, 6...)
            
            # Acciones
            sheet.write(position_y, col_pyg, acciones_pyg_cant, numerico)
            sheet.write(position_y, col_usd, acciones_usd_cant, numerico)
            position_y += 1
            
            # Bonos
            sheet.write(position_y, col_pyg, bonos_pyg_cant, numerico)
            sheet.write(position_y, col_usd, bonos_usd_cant, numerico)
            position_y += 1
            
            # Fondos
            sheet.write(position_y, col_pyg, fondos_pyg_cant, numerico)
            sheet.write(position_y, col_usd, fondos_usd_cant, numerico)
            position_y += 1
            
            # Negociabilidad
            sheet.write(position_y, col_pyg, negociabilidad_pyg_cant, numerico)
            sheet.write(position_y, col_usd, 0, numerico)  # No hay USD
            position_y += 1
            
            # Repos
            sheet.write(position_y, col_pyg, repos_pyg_cant, numerico)
            sheet.write(position_y, col_usd, repos_usd_cant, numerico)
            position_y += 1
            
            # Total General (suma por moneda)
            sheet.write(position_y, col_pyg, 
                       acciones_pyg_cant + bonos_pyg_cant + fondos_pyg_cant + 
                       negociabilidad_pyg_cant + repos_pyg_cant, 
                       numerico_total)
            sheet.write(position_y, col_usd,
                       acciones_usd_cant + bonos_usd_cant + fondos_usd_cant +
                       repos_usd_cant,
                       numerico_total)
            position_y += 1
            
            # Acciones físicas
            sheet.write(position_y, col_pyg, acciones_fisicas_pyg_cant, numerico)
            sheet.write(position_y, col_usd, 0, numerico)  # No hay USD
            position_y += 1
            
            # Custodia física
            sheet.write(position_y, col_pyg, custodia_pyg_cant, numerico)
            sheet.write(position_y, col_usd, custodia_usd_cant, numerico)
            position_y += 1
            
            # Futuro
            sheet.write(position_y, col_pyg, 0, numerico)  # No hay PYG
            sheet.write(position_y, col_usd, futuro_usd_cant, numerico)
            position_y += 1
            
            # Total Final
            sheet.write(position_y, col_pyg,
                       acciones_pyg_cant + bonos_pyg_cant + fondos_pyg_cant +
                       negociabilidad_pyg_cant + repos_pyg_cant +
                       acciones_fisicas_pyg_cant + custodia_pyg_cant,
                       numerico_total)
            sheet.write(position_y, col_usd,
                       acciones_usd_cant + bonos_usd_cant + fondos_usd_cant +
                       repos_usd_cant + custodia_usd_cant + futuro_usd_cant,
                       numerico_total)
            
            m += 1
            position_y += 1  # Ajuste para el siguiente mes