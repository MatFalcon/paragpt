import logging
import io
import xlsxwriter
import base64
from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)


class EstadoVencimiento(models.Model):
    _name = 'pbp.estado.vencimiento'
    _description = 'Estado para reporte de vencimientos'

    name = fields.Char(string='Nombre', required=True)
    value = fields.Char()

class IntrumentoVencimiento(models.Model):
    _name = 'pbp.instrumento.vencimiento'
    _description = 'Instrumentos para el reporte de vencimientos'

    name = fields.Char(string='Nombre', required=True)
    value = fields.Char()


class WizardFacturas(models.TransientModel):
    _name = 'reporte.cuadro'
    _description = 'Reporte Cuadro Revaluo'

    # estos campos crea nomas por si acaso
    reporte_capital = fields.Boolean(string="Reporte Avanzado")
    reporte_excel = fields.Binary(string="Reporte Excel", readonly=True)
    ## Campo
    def generar_reporte_cuadro(self):
        ### Preparar Excel ###
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # hojas
        hoja_caratura = workbook.add_worksheet("Repote Cuadro")

        # Formatos
        bold = workbook.add_format({'bold': True, 'font_name': 'Roboto'})
        center_format = workbook.add_format({'align': 'center', 'border': 1})
        center_format_sin_borde = workbook.add_format({'align': 'center'})
        subtitulo = workbook.add_format(
            {'color': '#ffffff', 'bold': True, 'bg_color': '#501e53', 'font_name': 'Roboto'})
        subtitulo_amarillo = workbook.add_format(
            {'color': '#ffffff', 'bold': True, 'bg_color': '#fbba00', 'font_name': 'Roboto'})
        titulo = workbook.add_format(
            {'color': '##ffffff', 'bold': True, 'bg_color': '#f2f2f2', 'font_name': 'Roboto', 'align': 'center'})
        titulo_oscuro = workbook.add_format(
            {'color': '#000000', 'bold': True, 'bg_color': '#cecece', 'font_name': 'Roboto'})
        titulo_oscuro2 = workbook.add_format({'color': '#000000', 'bg_color': '#cecece', 'align': 'center'})
        numerico = workbook.add_format({'num_format': True, 'align': 'right', 'font_name': 'Roboto'})
        numerico.set_num_format('#,##0')
        numerico_total = workbook.add_format(
            {'num_format': True, 'align': 'right', 'bold': True, 'font_name': 'Roboto'})
        fecha_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align': 'center', 'border': 1})

        # ejemplo header
        #t
        #o
        #m
        #m
        #y
        #p
        #u
        #t
        #o
        headers = [
            "Denominación cuenta contable", "Emisor", "Tipo",
            "Estado", "Casa Bolsa", "Serie", "Fecha Compra", "Fecha Vencimiento", "Instrumento",
            "Moneda", "Valor Actual en PYG",
        ]

        row = 1
        for a in range(1, 10):
            # se escribe a partir de la fila 2, solo en la columna A (creo)
            hoja_caratura.write(row, 0) #la hoja se creo arriba


        # seteaR un anchSo de las colunmas
        hoja_caratura.set_column('A:A', 40)
        hoja_caratura.set_column('B:D', 20)
        workbook.close()
        output.seek(0)
        # Guardar el archivo en el campo `reporte_excel`
        self.reporte_excel = base64.b64encode(output.getvalue())
        self.reporte_nombre = f"Reporte_Devengamiento.xlsx"


        return {
            'type': 'ir.actions.act_url',
            'url': f'/download/reporte_vencimientos/{self.id}', # controlador definido en controllers
            'target': 'self',
        }




    fecha_inicio = fields.Date(string="Fecha Inicial")
    fecha_fin = fields.Date(string="Fecha Final")
    fecha_plazo = fields.Date(string="Fecha Plazo")
    plazo = fields.Selection(
        selection=[
            ('corto', 'Corto Plazo'),
            ('largo', 'Largo Plazo'),
        ]
    )

    amortizacion = fields.Selection(
        selection=[
            ('inicio', 'Inicio'),
            ('vtoInt', 'Vto.Interes'),
            ('pagocap', 'Pago de Capital'),
        ]
    )
    currency_id = fields.Many2one("res.currency")
    cambio_utilizado = fields.Float(string="Cotizacion")
    state_ids = fields.Many2many('pbp.estado.vencimiento', string='Estados')

    state = fields.Selection([('vencido', 'Vencido'), ('cobrado', 'Cobrado'), ('pendiente', 'Por Cobrar')])
    instrumentos_ids = fields.Many2many("pbp.instrumento.vencimiento", string="Instrumentos")
    instrumento = fields.Selection(
        selection=[
            ('acciones', 'Acciones'),
            ('bonos', 'Bonos'),
            ('bonos_cartulares', 'Bonos Cartulares'),
            ('bonos_corporativos', 'Bonos Corporativos'),
            ('bonos_del_tesoro', 'Bonos del Tesoro'),
            ('bonos_financieros', 'Bonos Financieros'),
            ('bonos_subordinados', 'Bonos Subordinados'),
            ('cda', 'CDA'),
            ('fondos', 'Fondos'),
        ],
    )
    reporte_capital = fields.Boolean(string="Reporte Avanzado")
    reporte_excel = fields.Binary(string="Reporte Excel", readonly=True)
    reporte_nombre = fields.Char(string="Nombre del Archivo", readonly=True)

    def generar_reporte_vencimientos(self):
        # cuentas largo plazo para bonos y cda
        bono_lp_pyg = self.env['account.account'].search([('code', '=', '12301')])
        bono_lp_usd = self.env['account.account'].search([('code', '=', '12302')])
        cda_lp_pyg = self.env['account.account'].search([('code', '=', '12306')])
        cda_lp_usd = self.env['account.account'].search([('code', '=', '12313')])
        dominio = []


        dominio.append(('instrumento', '!=', False))
        #### Preparar Filtro ####
        if self.fecha_inicio and not self.reporte_capital:
            dominio.append(('fecha_vencimiento', '>=', self.fecha_inicio))

        if self.fecha_fin and not self.reporte_capital:
            dominio.append(('fecha_vencimiento', '<=', self.fecha_fin))

        # definir cuenta LP o CP
        hoy = fields.Date.today()
        # si se selecciona una fecha_plazo se calcula corto y largo plazo en base a eso
        if self.fecha_plazo:
            fin_ano_actual = self.fecha_plazo.replace(month=12, day=31)
        else:
            fin_ano_actual = hoy.replace(month=12, day=31)

        # para obtener corto o largo plazo
        if self.plazo == 'corto' and not self.reporte_capital:
            dominio.append(('fecha_vencimiento', '<=', fin_ano_actual))
        if self.plazo == 'largo' and not self.reporte_capital:
            dominio.append(('fecha_vencimiento', '>', fin_ano_actual))

        # si se selecciona reporte_capital
        # las el filtro de fecha se hace por fecha de compra
        if self.plazo and self.reporte_capital:
            if self.fecha_fin:
                dominio.append(('registros.fecha_compra', '<=', self.fecha_fin))
            if self.plazo == 'corto':
                dominio.append(('fecha_vencimiento', '<=', fin_ano_actual))
            if self.plazo == 'largo':
                dominio.append(('fecha_vencimiento', '>', fin_ano_actual))

        # para filtar por los estados de los cobros de vencimientos y capital
        if self.state_ids:
            estados_filtro = []
            for state_select in self.state_ids:
                estados_filtro.append(state_select.value)
            dominio.append(('state', 'in', estados_filtro))

        # para filtar por el tipo de vencimiento (interes, capital)
        if self.amortizacion:
            dominio.append(('amortizacion', '=', self.amortizacion))

        # para filtar por moneda
        if self.currency_id:
            dominio.append(("currency_id", '=', self.currency_id.id))

        #para filtrar por instrumentos
        if self.instrumentos_ids:
            instrumentos_select = []
            for ins in self.instrumentos_ids:
                instrumentos_select.append(ins.value)
            dominio.append(('instrumento', 'in', instrumentos_select))

        # limita los registros segun la fecha de compra del instrumento
        # aun asi traeria los vencimientos que superen fecha_fin
        # esto permite ver los registros que se tenia en esa fecha
        if self.reporte_capital and self.fecha_fin:
            dominio.append(('registros.fecha_compra', '<=', self.fecha_fin))
        #### Preparar Filtro Fin ####

        vencimientos_cartera = self.env['pbp.vencimiento_capital_interes'].search(dominio)
        _logger.info(f"Dominio: {dominio}")

        ### Preparar Excel ###
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # hojas
        hoja_caratura = workbook.add_worksheet("Reporte Tabla Cruce Contable")
        hoja_cartera = workbook.add_worksheet("Cartera")

        # Formatos
        bold = workbook.add_format({'bold': True, 'font_name': 'Roboto'})
        center_format = workbook.add_format({'align': 'center', 'border': 1})
        center_format_sin_borde = workbook.add_format({'align': 'center'})
        subtitulo = workbook.add_format(
            {'color': '#ffffff', 'bold': True, 'bg_color': '#501e53', 'font_name': 'Roboto'})
        subtitulo_amarillo = workbook.add_format(
            {'color': '#ffffff', 'bold': True, 'bg_color': '#fbba00', 'font_name': 'Roboto'})
        titulo = workbook.add_format(
            {'color': '##ffffff', 'bold': True, 'bg_color': '#f2f2f2', 'font_name': 'Roboto', 'align': 'center'})
        titulo_oscuro = workbook.add_format(
            {'color': '#000000', 'bold': True, 'bg_color': '#cecece', 'font_name': 'Roboto'})
        titulo_oscuro2 = workbook.add_format({'color': '#000000', 'bg_color': '#cecece', 'align': 'center'})
        numerico = workbook.add_format({'num_format': True, 'align': 'right', 'font_name': 'Roboto'})
        numerico.set_num_format('#,##0')
        numerico_total = workbook.add_format(
            {'num_format': True, 'align': 'right', 'bold': True, 'font_name': 'Roboto'})
        fecha_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align': 'center', 'border': 1})

        ### Preparar Excel Fin ###

        ### Variables auxiliares ###

        cruce_contable_valores = {

        }

        ### Registros de Cartera ###
        # Definir encabezados
        headers = [
            "Denominación cuenta contable", "Emisor", "Tipo",
            "Estado", "Casa Bolsa", "Serie", "Fecha Compra", "Fecha Vencimiento", "Instrumento",
            "Moneda", "Valor Actual en PYG",
        ]
        es_dolar = False
        if self.currency_id:
            if self.currency_id.id != 155:
                es_dolar = True
        else:
            es_dolar = True

        if es_dolar:
            headers.append("Valor Actual en USD")

        # Hoja 2 - Se escribe la cabecera
        hoja_cartera.write_row(0, 0, headers, subtitulo)
        row = 1
        print(dominio)
        print("Vencimientos seleccionados", len(vencimientos_cartera))
        for vencimiento in vencimientos_cartera:
            # C.A
            moneda = "PYG" if vencimiento.registros.currency_id.id == 155 else "USD"
            moneda_cruce = "Guaranies" if vencimiento.registros.currency_id.id == 155 else "Dolares Americanos"

            valor_actual_pyg = vencimiento.valor_actual_pyg
            # _logger.info(f"id {vencimiento.id}")
            # Si no tiene toma directamente del vencimiento
            valor_actual_usd = vencimiento.valor_actual_usd
            # Si se definio la cotizacion el el reporte se calcula en base a eso en valor_actual_usd
            if self.cambio_utilizado and self.cambio_utilizado > 0:
                if vencimiento.registros.currency_id.id == 155:
                    valor_actual_pyg = vencimiento.total
                    valor_actual_usd = valor_actual_pyg / self.cambio_utilizado
                else:
                    valor_actual_pyg = vencimiento.total * self.cambio_utilizado
                    valor_actual_usd = vencimiento.total

            # _logger.info(f"valor_actual_pyg 2: {valor_actual_pyg}")

            # se preparan las cuentas segun la fecha (intereses)
            if vencimiento.fecha_vencimiento > fin_ano_actual: #largo plazo
                cuenta = vencimiento.registros.initial_debit_account_id_lp.name
            else: # corto plazo
                cuenta = vencimiento.registros.initial_debit_account_id.name

            # se preparan las cuentas segun la fecha (capital)
            # solo tenemos cuenta para largo plazo
            if vencimiento.amortizacion == 'pagocap':
                if vencimiento.fecha_vencimiento > fin_ano_actual:  # largo plazo
                    # segun instrumentos se toman las cuentas inicializadas en la primera parte de esta funcion (bono cda)
                    if 'bono' in vencimiento.registros.instrumento:
                        if moneda == "PYG":
                            cuenta = bono_lp_pyg.name
                        else:
                            cuenta = bono_lp_usd.name
                    elif 'cda' in vencimiento.registros.instrumento:
                        if moneda == "PYG":
                            cuenta = cda_lp_pyg.name
                        else:
                            cuenta = cda_lp_usd.name
                else:
                    cuenta = vencimiento.cuenta.name

            # se inicializa en el dic la cuenta con la moneda y los estados de cobro inicializados en 0
            # estos se iran sumando con cada iteracion
            if cuenta not in cruce_contable_valores.keys():
                cruce_contable_valores[cuenta] = {'moneda': moneda_cruce,
                                                  'total_pendiente': 0,
                                                  'total_cobrado': 0,
                                                  'total_vencido': 0}
                # _logger.info(f"Cuentas: {cruce_contable_valores}")
                # _logger.info(f"Se aniadio: {cuenta}")

            # Hoja 2 - Escritura del registro
            hoja_cartera.write(row, 0, cuenta, center_format)
            hoja_cartera.write(row, 1, vencimiento.registros.emision, center_format)
            hoja_cartera.write(row, 2, vencimiento.amortizacion, center_format)
            hoja_cartera.write(row, 3, vencimiento.state, center_format)
            hoja_cartera.write(row, 4,
                               vencimiento.registros.casa_bolsa.name if vencimiento.registros.casa_bolsa else vencimiento.registros.emision,
                               center_format)
            hoja_cartera.write(row, 5, vencimiento.name, center_format)
            hoja_cartera.write(row, 6, vencimiento.registros.fecha_compra, fecha_format)
            hoja_cartera.write(row, 7, vencimiento.fecha_vencimiento, fecha_format)
            hoja_cartera.write(row, 8, vencimiento.registros.instrumento, center_format)
            hoja_cartera.write(row, 9, moneda, center_format)
            hoja_cartera.write(row, 10, valor_actual_pyg, center_format)
            # print(vencimiento.total, vencimiento.valor_actual_pyg, vencimiento.valor_actual_usd)
            if es_dolar:
                hoja_cartera.write(row, 11, valor_actual_usd, center_format)

            # sumar cruce contable - aqui se va sumando los valores del dic
            monto_cruce = valor_actual_pyg
            if vencimiento.state == 'vencido':
                # si esta marcado reporte avanzado los que superan la fecha del plazo, deberian estar en estado por cobrar
                #                           si es menor a la fecha trae el estado original
                if self.reporte_capital and vencimiento.fecha_vencimiento < self.fecha_plazo:
                    cruce_contable_valores[cuenta]['total_vencido'] = cruce_contable_valores[cuenta][
                                                                          'total_vencido'] + monto_cruce
                else:
                    cruce_contable_valores[cuenta]['total_pendiente'] = cruce_contable_valores[cuenta][
                                                                          'total_pendiente'] + monto_cruce
            # lo mismo para los cobrados, deben estar como pendientes ya que se trata de un reporte en pasado
            elif vencimiento.state == 'cobrado':
                #                           si es menor a la fecha trae el estado original
                if self.reporte_capital and vencimiento.fecha_vencimiento < self.fecha_plazo:
                    cruce_contable_valores[cuenta]['total_cobrado'] = cruce_contable_valores[cuenta][
                                                                          'total_cobrado'] + monto_cruce
                else:
                    cruce_contable_valores[cuenta]['total_pendiente'] = cruce_contable_valores[cuenta][
                                                                          'total_pendiente'] + monto_cruce
                #_logger.info(f"Sumas Cobrado: {cruce_contable_valores[cuenta]['total_cobrado']}")
            elif vencimiento.state == 'pendiente' and (not self.fecha_plazo and vencimiento.fecha_vencimiento > fin_ano_actual):
                cruce_contable_valores[cuenta]['total_pendiente'] = cruce_contable_valores[cuenta][
                                                                        'total_pendiente'] + monto_cruce
            else:
                cruce_contable_valores[cuenta]['total_pendiente'] = cruce_contable_valores[cuenta][
                                                                        'total_pendiente'] + monto_cruce

            row += 1

        # seteaR un anchSo de las colunmas
        hoja_cartera.set_column('A:B', 40)
        hoja_cartera.set_column('C:D', 15)
        hoja_cartera.set_column('E:E', 35)
        hoja_cartera.set_column('F:J', 20)
        hoja_cartera.set_column('F:K', 35)

        ### Registros de Cartera Fin###

        ### Preparar Caratula - Hoja 1 ###
        headers = [
            "Denominación cuenta contable", "Moneda", "Estado", "Total"
        ]

        for col in range(0, 4):
            hoja_caratura.write(1, col, "", titulo)
            hoja_caratura.write(2, col, "", titulo)
            hoja_caratura.write(3, col, "", titulo)

        hoja_caratura.write_row(4, 0, headers, titulo_oscuro)

        row = 5
        # se itera el dic de las cuentas con sus valores inicializados en el anterior bucle
        for cuenta in cruce_contable_valores.keys():
            # _logger.info(f"Cuentas: {cuenta}")
            hoja_caratura.write(row, 0, cuenta, center_format_sin_borde)
            totales = 0
            if cruce_contable_valores[cuenta]['total_vencido'] > 0:
                hoja_caratura.write(row, 1, cruce_contable_valores[cuenta]['moneda'], center_format_sin_borde)
                hoja_caratura.write(row, 2, "Vencido", center_format_sin_borde)
                hoja_caratura.write(row, 3, round(cruce_contable_valores[cuenta]['total_vencido'], 2),
                                    center_format_sin_borde)
                totales += cruce_contable_valores[cuenta]['total_vencido']
                row += 1
            if cruce_contable_valores[cuenta]['total_cobrado'] > 0:
                hoja_caratura.write(row, 1, cruce_contable_valores[cuenta]['moneda'], center_format_sin_borde)
                hoja_caratura.write(row, 2, "Cobrado", center_format_sin_borde)
                hoja_caratura.write(row, 3, round(cruce_contable_valores[cuenta]['total_cobrado'], 2),
                                    center_format_sin_borde)
                totales += cruce_contable_valores[cuenta]['total_cobrado']
                row += 1
            if cruce_contable_valores[cuenta]['total_pendiente'] > 0:
                hoja_caratura.write(row, 1, cruce_contable_valores[cuenta]['moneda'], center_format_sin_borde)
                hoja_caratura.write(row, 2, "Pendiente", center_format_sin_borde)
                hoja_caratura.write(row, 3, round(cruce_contable_valores[cuenta]['total_pendiente'], 2),
                                    center_format_sin_borde)
                totales += cruce_contable_valores[cuenta]['total_pendiente']
                row += 1
            hoja_caratura.write(row, 0, "", titulo_oscuro2)
            hoja_caratura.write(row, 1, "", titulo_oscuro2)
            hoja_caratura.write(row, 2, "Total", titulo_oscuro2)
            hoja_caratura.write(row, 3, round(totales, 2), titulo_oscuro2)

            row += 1
        # seteaR un anchSo de las colunmas
        hoja_caratura.set_column('A:A', 40)
        hoja_caratura.set_column('B:D', 20)
        workbook.close()
        output.seek(0)
        # Guardar el archivo en el campo `reporte_excel`
        self.reporte_excel = base64.b64encode(output.getvalue())
        self.reporte_nombre = f"Reporte_Devengamiento.xlsx"

        return {
            'type': 'ir.actions.act_url',
            'url': f'/download/reporte_vencimientos/{self.id}', # controlador definido en controllers
            'target': 'self',
        }



