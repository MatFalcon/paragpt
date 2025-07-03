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
    _name = 'pbp.wizard.vencimientos.report'
    _description = 'Wizard Vencimientos de Cartera Report'

    fecha_inicio = fields.Date(string="Fecha Inicial")
    fecha_fin = fields.Date(string="Fecha Final")
    fecha_compra = fields.Date(string="Hasta Fecha Compra")
    fecha_vencimiento = fields.Date(string="Hasta Fecha Vencimiento")
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


    @api.onchange('fecha_compra')
    def _onchange_fecha_fin_set_cotizacion(self):
        """
        Al cambiar 'fecha_fin', buscamos la tasa de USD-Venta para ese día
        y dejamos dicho valor en cambio_utilizado. Si el usuario quiere otro
        valor, puede editarlo directamente en la casilla.
        """
        #_logger = logging.getLogger(__name__)
        #_logger.info('Iniciando _onchange_fecha_fin_set_cotizacion')
        #_logger.info('Fecha compra: %s', self.fecha_compra)
        #_logger.info('Cambio utilizado actual: %s', self.cambio_utilizado)
        
        if not self.fecha_compra:
            _logger.info('No hay fecha de compra seleccionada, retornando')
            return

        usd_venta = self.env['res.currency'].search([('name','=','USD-Venta')], limit=1)
        if not usd_venta:
            return

        tasa = self.env['res.currency.rate'].search([
            ('currency_id','=', usd_venta.id),
            ('name','<=', self.fecha_compra)
        ], order='name desc', limit=1)

        if tasa:
            _logger.info('Tasa encontrada: %s', tasa.set_venta)
            self.cambio_utilizado = tasa.rate
        else:
            _logger.warning('No se encontro tasa para la fecha especificada')
            self.cambio_utilizado = 0.0
        
        _logger.info('Finalizando _onchange_fecha_fin_set_cotizacion. Nuevo cambio utilizado: %s', self.cambio_utilizado)
        if not self.fecha_compra:
            return

        usd_venta = self.env['res.currency'].search([('name','=','USD-Venta')], limit=1)
        if not usd_venta:
            return

        tasa = self.env['res.currency.rate'].search([
            ('currency_id','=', usd_venta.id),
            ('name','<=', self.fecha_compra )      \
        ], order='name desc', limit=1)

        if tasa:
            self.cambio_utilizado = tasa.set_venta
        else:
            self.cambio_utilizado = 0.0

    def guardar_reporte(self):
        self.generar_reporte_vencimientos(guardar_reporte=True)

    def generar_reporte_vencimientos(self, guardar_reporte=False):
        """
            Genera un excel o reporte contable, de los vencimientos (ingresos) de cartera propia.
            Es retroactivo, es decir se puede elejir un periodo en el que se basa definir si un ingreso
            es corto o largo plazo.

        """
        dominio = []
        # cuentas largo plazo para bonos y cda para los cobros de capitales
        bono_lp_pyg = self.env['account.account'].search([('code', '=', '12301')])
        bono_lp_usd = self.env['account.account'].search([('code', '=', '12302')])
        cda_lp_pyg = self.env['account.account'].search([('code', '=', '12306')])
        cda_lp_usd = self.env['account.account'].search([('code', '=', '12313')])

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
            {'color': '##ffffff', 'bold': True, 'bg_color': '#f2f2f2', 'font_name': 'Roboto', 'align': 'center','color': '#000000'})
        titulo_oscuro = workbook.add_format(
            {'color': '#000000', 'bold': True, 'bg_color': '#cecece', 'font_name': 'Roboto'})
        titulo_oscuro2 = workbook.add_format({'color': '#000000', 'bg_color': '#cecece', 'align': 'center'})
        numerico = workbook.add_format({'num_format': True, 'align': 'right', 'font_name': 'Roboto'})
        numerico.set_num_format('#,##0')
        numerico_total = workbook.add_format(
            {'num_format': True, 'align': 'right', 'bold': True, 'font_name': 'Roboto'})
        fecha_format = workbook.add_format({'num_format': 'yyyy-mm-dd', 'align': 'center', 'border': 1})

        formato_entero = workbook.add_format({
            'num_format': '#,##0',      # 0 decimales, separador de miles
            'align': 'right',
            'font_name': 'Roboto',
            
        })
        formato_entero_hoja2 = workbook.add_format({
            'num_format': '#,##0',      # 0 decimales, separador de miles
            'align': 'right',
            'font_name': 'Roboto',
            'border': 1,                   # borde fino en todas las celdas
            'border_color': '#000000', 
            
        })

        formato_entero_oscuro = workbook.add_format({
            'num_format': '#,##0',      
            'color':      '#000000',     
            'bg_color':   '#cecece',     
            'align':      'right',      
            'font_name':  'Roboto',      
        })
        formato_decimal = workbook.add_format({
            'num_format': '#,##0.00',   # 2 decimales, separador de miles
            'align': 'right',
            'font_name': 'Roboto',
        })
        formato_decimal_gris = workbook.add_format({
            'num_format': '#,##0.00',   # 2 decimales, separador de miles
            'align': 'right',
            'color':      '#000000',     
            'bg_color':   '#cecece',     
            'align':      'right',      
            'font_name':  'Roboto',  
        })
        formato_decimal_hoja2 = workbook.add_format({
            'num_format': '#,##0.00',   # 2 decimales, separador de miles
            'align': 'right',
            'font_name': 'Roboto',
            'border': 1,                   # borde fino en todas las celdas
            'border_color': '#000000', 
        })
        ### Preparar Excel Fin ###

        ### INICIO FILTROS ###

        # referencia para el periodo fiscal, en base a esta fecha se asume si un ingreso es a corto o largo plazo
        hoy = fields.Date.today()
        if self.fecha_plazo:
            fin_ano_actual = self.fecha_plazo.replace(month=12, day=31)
        else:
            fin_ano_actual = hoy.replace(month=12, day=31)
        
        # fecha fin (fecha_compra) cuando se requiere que sea retroactivo, convina con fecha_plazo
        if self.fecha_compra:
            dominio.append(('fecha_compra', '<=', self.fecha_compra))
        # para filtar por los estados de los cobros de vencimientos y capital
        # cuado es un reporte capital (retroactivo) el estado de los vencimientos se evalua de otra forma
        if self.state_ids:
            estados_filtro = []
            for state_select in self.state_ids:
                estados_filtro.append(state_select.value)
        # fecha fin (vencimiento) solo si es un reporte no retroactivo
        #if self.fecha_fin and not self.reporte_capital:
             #dominio.append(('fecha_vencimiento', '<=', self.fecha_fin))

        # para filtrar por moneda
        if self.currency_id:
            dominio.append(("currency_id", '=', self.currency_id.id))

        # para filtrar por instrumentos
        if self.instrumentos_ids:
            instrumentos_select = []
            for ins in self.instrumentos_ids:
                instrumentos_select.append(ins.value)
            dominio.append(('instrumento', 'in', instrumentos_select))

        _logger.info(f"DOMINIO: {dominio}")
        ### FIN FILTROS ###
        vencimientos_cartera = self.env['pbp.vencimiento_capital_interes'].search(dominio)


        ### VARIABLE AUXILIAR ###
        # en este dic se guardan los subtotales para el resumen
        cruce_contable_valores = {
         #   'cuenta':{
         #       'moneda':155,
         #       'total_pendiente':00
         #       ....
         #       }
        }

        ### CABECERA PARA LA HOJA 2
        headers = ["Cuenta",
            "Denominación cuenta contable", "Emisor", "Tipo",
            "Estado", "Casa Bolsa", "Serie", "Fecha Compra", "Fecha Vencimiento","Calificacion","Tasa", "Instrumento",
            "Moneda", "Valor Actual en PYG",
        ]
        
        es_dolar = False
        if self.currency_id:
            if self.currency_id.id != 155:
                es_dolar = True
        else:
            es_dolar = True

        # ESTA COLUMNA SOLO SE AGREGA SI NO SE ELIJIO NINGUNA MONEDA O SE ELIJIO DOLARES
        if es_dolar:
            headers.append("Valor Actual en USD")

        # HOJA 2 - SE ESCRIBE LA CABECERA
        hoja_cartera.write_row(0, 0, headers, subtitulo)
        row = 1
        print(dominio)
        print("Vencimientos seleccionados", len(vencimientos_cartera))
        subtotal_global_pyg = 0
        subtotal_global_usd = 0
        for vencimiento in vencimientos_cartera:
            if self.state_ids:
                if vencimiento.state not in estados_filtro:
                    if self.fecha_plazo and vencimiento.fecha_vencimiento > self.fecha_plazo:
                        pass
                    else:    
                        continue
            if self.fecha_vencimiento:
                if vencimiento.fecha_vencimiento > self.fecha_vencimiento:
                    continue
            # C.A
            moneda = "PYG" if vencimiento.registros.currency_id.id == 155 else "USD"
            moneda_cruce = "Guaranies" if vencimiento.registros.currency_id.id == 155 else "Dolares Americanos"
            
            valor_actual_pyg = vencimiento.valor_actual_pyg
            valor_actual_usd = vencimiento.valor_actual_usd
            # Si se definio la cotizacion el el reporte se calcula en base a eso el valor_actual_usd
            # y la conversion a guaranies
            if self.cambio_utilizado and self.cambio_utilizado > 0:
                if vencimiento.registros.currency_id.id == 155:
                    valor_actual_pyg = vencimiento.total
                    valor_actual_usd = valor_actual_pyg / self.cambio_utilizado
                else:
                    valor_actual_pyg = vencimiento.total * self.cambio_utilizado
                    valor_actual_usd = vencimiento.total


            # se preparan las cuentas segun la fecha (intereses)
            if vencimiento.fecha_vencimiento > fin_ano_actual: #largo plazo
                code = vencimiento.registros.initial_debit_account_id_lp.code
                cuenta = vencimiento.registros.initial_debit_account_id_lp.name
            else: # corto plazo
                cuenta = vencimiento.registros.initial_debit_account_id.name
                code = vencimiento.registros.initial_debit_account_id.code

            # se preparan las cuentas segun la fecha (capital)
            # solo tenemos cuenta para largo plazo
            if vencimiento.amortizacion == 'pagocap':
                if vencimiento.fecha_vencimiento > fin_ano_actual:  # largo plazo
                    # segun instrumentos se toman las cuentas inicializadas en la primera parte de esta funcion (bono cda)
                    if 'bono' in vencimiento.registros.instrumento:
                        if moneda == "PYG":
                            cuenta = bono_lp_pyg.name
                            code = bono_lp_pyg.code
                        else:
                            cuenta = bono_lp_usd.name
                            code = bono_lp_usd.code
                    elif 'cda' in vencimiento.registros.instrumento:
                        if moneda == "PYG":
                            cuenta = cda_lp_pyg.name
                            code = cda_lp_pyg.code
                        else:
                            cuenta = cda_lp_usd.name
                            code = cda_lp_usd.code
                else:
                    cuenta = vencimiento.cuenta.name
                    code = vencimiento.cuenta.code

            # se inicializa en el dic la cuenta con la moneda y los estados de cobro inicializados en 0
            # estos se iran sumando con cada iteracion
            if cuenta not in cruce_contable_valores.keys():
                cruce_contable_valores[cuenta] = {'moneda': moneda_cruce,
                                                  'total_pendiente': 0,
                                                  'total_cobrado': 0,
                                                  'total_vencido': 0,
                                                  'code': code
                                                  }

            # Hoja 2 - Escritura del registro
            hoja_cartera.write(row, 0, code, center_format)
            hoja_cartera.write(row, 1, cuenta, center_format)
            hoja_cartera.write(row, 2, vencimiento.registros.emision, center_format)
            hoja_cartera.write(row, 3, vencimiento.amortizacion, center_format)
            hoja_cartera.write(row, 4, vencimiento.state, center_format)
            hoja_cartera.write(row, 5,
                               vencimiento.registros.casa_bolsa.name if vencimiento.registros.casa_bolsa else vencimiento.registros.emision,
                               center_format)
            hoja_cartera.write(row, 6, vencimiento.name, center_format)
            hoja_cartera.write(row, 7, vencimiento.registros.fecha_compra, fecha_format)
            hoja_cartera.write(row, 8, vencimiento.fecha_vencimiento, fecha_format)
            hoja_cartera.write(row, 9, vencimiento.registros.calificacion_riesgo or '', center_format)
            hoja_cartera.write(row, 10, vencimiento.registros.tasa_interes, center_format)
            hoja_cartera.write(row, 11, vencimiento.registros.instrumento, center_format)
            hoja_cartera.write(row, 12, moneda, center_format)
            hoja_cartera.write(row, 13, valor_actual_pyg, formato_entero_hoja2)
            # print(vencimiento.total, vencimiento.valor_actual_pyg, vencimiento.valor_actual_usd)
            if es_dolar:
                hoja_cartera.write(row, 14, valor_actual_usd, formato_decimal_hoja2)

            monto_cruce = valor_actual_pyg
            
            subtotal_global_pyg += valor_actual_pyg
            subtotal_global_usd += valor_actual_usd
            # segun el tipo de reporte se suman por los estados de los vencimientos o ingresos
             #if self.fecha_plazo and self.reporte_capital:
             #   # en esta parte, en lugar de tomar los estados tal cual, se asume que cuando estan por debajo de la fecha fin
             #   # o es menor a fecha fin, ya esta cobrado, y el resto que esta por encima es por cobrar.
             #   if self.fecha_plazo < vencimiento.fecha_vencimiento:
             #       cruce_contable_valores[cuenta]['total_pendiente'] = cruce_contable_valores[cuenta][
             #                                                             'total_pendiente'] + monto_cruce
             #   else:
             #       cruce_contable_valores[cuenta]['total_cobrado'] = cruce_contable_valores[cuenta][
             #                                                             'total_cobrado'] + monto_cruce
                                                           
            if True:
                # en esta parte se toma los estados originales y ya.
                if vencimiento.state == 'vencido':
                    cruce_contable_valores[cuenta]['total_vencido'] = cruce_contable_valores[cuenta][
                                                                          'total_vencido'] + monto_cruce
                elif vencimiento.state == 'cobrado':
                    cruce_contable_valores[cuenta]['total_cobrado'] = cruce_contable_valores[cuenta][
                                                                          'total_cobrado'] + monto_cruce
                elif vencimiento.state == 'pendiente'   :
                    cruce_contable_valores[cuenta]['total_pendiente'] = cruce_contable_valores[cuenta][
                                                                          'total_pendiente'] + monto_cruce
            row += 1

        ### LOGICA PARA FONDOS DE INVERSION ###
        domain_fondos = [('instrumento','in', ('fondos', 'acciones'))]

        if self.fecha_compra:
            # se por la fecha de compra, luego hay que filtrar tambien los movimientos
            domain_fondos.append(('fecha_compra', '<=', self.fecha_compra))
        fondos = self.env['pbp.cartera_inversion'].search(domain_fondos)
        # primero se carga o se suma la inversion inicial, luego le vamos aniadiendo y restando segun los rendimientos o movimientos
        # los rendimientos suman al valor de la inversion
        # los movimientos pueden sumar o restar para los casos de retiros
        for fondo in fondos:
            # validamos que moneda es
            is_usd = (fondo.currency_id.id != 155)
            # para escribirlo en el excel en formato texto
            moneda = "USD" if is_usd else "PYG"
            moneda_cruce = "Dolares Americanos" if is_usd else "Guaranies"

            # inicializamos la cuenta que se va a utilizar
            cuenta = fondo.inversion_account_id and fondo.inversion_account_id.name or 'Sin Cuenta'
            code = fondo.inversion_account_id.code or 'Sin Cuenta'
            if cuenta not in cruce_contable_valores:
                cruce_contable_valores[cuenta] = {
                    'moneda': moneda_cruce,
                    'total_pendiente': 0,
                    'total_cobrado': 0,
                    'total_vencido': 0,
                    'total_inversion':0,
                    'code': code
                }

            # cargamos primero la inversion inicial
            if is_usd:
                monto_inicial_usd = fondo.importe_valorizado
                if self.cambio_utilizado:
                    monto_inicial_pyg = fondo.importe_valorizado * self.cambio_utilizado
                else:
                    monto_inicial_pyg = fondo.importe_valorizado * fondo.cambio_utilizado
            else:
                monto_inicial_pyg = fondo.importe_valorizado
                if self.cambio_utilizado:
                    monto_inicial_usd = fondo.importe_valorizado / self.cambio_utilizado
                else:
                    try:
                        monto_inicial_usd = fondo.importe_valorizado / fondo.cambio_utilizado
                    except ZeroDivisionError:
                        monto_inicial_usd = 0

            # se suma a la cuenta
            cruce_contable_valores[cuenta]['total_inversion'] += monto_inicial_pyg
            # se escribe la fila correspondiente para la inversion inicial

            hoja_cartera.write(row, 0, code,                           center_format)
            hoja_cartera.write(row, 1, cuenta,                           center_format)
            hoja_cartera.write(row, 2, fondo.partner_id.name,           center_format)  
            hoja_cartera.write(row, 3, 'Inversion Inicial',                        center_format)  
            hoja_cartera.write(row, 4, '',                               center_format) 
            hoja_cartera.write(row, 5, fondo.partner_id.name or '',     center_format)  
            hoja_cartera.write(row, 6, fondo.serie,                      center_format) 
            hoja_cartera.write(row, 7, fondo.fecha_compra,               fecha_format)  
            hoja_cartera.write(row, 8, '',                               center_format) 
            hoja_cartera.write(row, 9, fondo.calificacion_riesgo,               fecha_format)  
            hoja_cartera.write(row, 10, '',    fecha_format) # tasa
            hoja_cartera.write(row, 11, fondo.instrumento,                center_format) 
            hoja_cartera.write(row, 12, moneda,                          center_format)  
            hoja_cartera.write(row,13, monto_inicial_pyg,                        formato_entero_hoja2)  
            hoja_cartera.write(row,14, monto_inicial_usd ,                        formato_decimal_hoja2)  
            row += 1
            # vamos a continuar con los movimientos (primero los periodos donde estan los rendimientos)
            subtotal_global_usd += monto_inicial_usd
            subtotal_global_pyg += monto_inicial_pyg
            # Iterar los periodos validos (fecha_inicio <= fecha_fin)
            if self.fecha_vencimiento:
                periodos_validos = fondo.fondo_periodo_ids.filtered(
                        lambda p: p.fecha_inicio <= self.fecha_vencimiento
                    )
            else:
                periodos_validos = fondo.fondo_periodo_ids

            for periodo in periodos_validos:
                # Filtrar vencimientos del periodo cuyo vencimiento.fecha <= fecha_fin si se elijio una fecha_fin
                if self.fecha_vencimiento:
                    vencimientos_validos = periodo.vencimiento_ids.filtered(
                            lambda v: v.fecha <= self.fecha_vencimiento and v.state == 'registrado'
                        )
                else:
                    vencimientos_validos = periodo.vencimiento_ids#.filtered(
                        #    lambda v: v.state == 'registrado'
                        #)
                for vencimiento in vencimientos_validos:
                    monto_rendimiento_pyg = 0
                    monto_rendimiento_usd = 0
                    if is_usd:
                        monto_rendimiento_usd = vencimiento.monto_rendimiento
                        if self.cambio_utilizado:
                            monto_rendimiento_pyg = vencimiento.monto_rendimiento * self.cambio_utilizado
                        else:
                            monto_rendimiento_pyg = vencimiento.monto_rendimiento  * fondo.cambio_utilizado
                    else:
                        monto_rendimiento_pyg = vencimiento.monto_rendimiento
                        if self.cambio_utilizado:
                            monto_inicial_usd = vencimiento.monto_rendimiento / self.cambio_utilizado
                        else:
                            try:
                                monto_rendimiento_usd = vencimiento.monto_rendimiento / fondo.cambio_utilizado
                            except ZeroDivisionError:
                                monto_rendimiento_usd = 0
                    if monto_inicial_pyg == 0:
                        continue
                    cruce_contable_valores[cuenta]['total_inversion'] += monto_rendimiento_pyg
        
                    # escritura en excel            
                    hoja_cartera.write(row, 0, code,                           center_format)
                    hoja_cartera.write(row, 1, cuenta,                           center_format)
                    hoja_cartera.write(row, 2, fondo.partner_id.name,           center_format)  
                    hoja_cartera.write(row, 3, f'Rendimiento {fondo.serie}',                        center_format)  
                    hoja_cartera.write(row, 4, '',                               center_format) # estado
                    hoja_cartera.write(row, 5, fondo.partner_id.name or '',     center_format)  
                    hoja_cartera.write(row, 6, fondo.serie,                      center_format) 
                    hoja_cartera.write(row, 7, fondo.fecha_compra,               fecha_format)  
                    hoja_cartera.write(row, 8, vencimiento.fecha,    fecha_format) # fecha de vencimiento 
                    hoja_cartera.write(row, 9, periodo.cartera_id.calificacion_riesgo or '',    fecha_format) 
                    hoja_cartera.write(row, 10, vencimiento.tasa_mensual if vencimiento.tasa_mensual > 0 else '',    center_format)
                    hoja_cartera.write(row, 11, "fondos" if periodo.cartera_id.instrumento == 'fondos' else 'acciones',                center_format) 
                    hoja_cartera.write(row, 12, moneda,                          center_format)  
                    hoja_cartera.write(row,13, monto_rendimiento_pyg,                        formato_entero_hoja2)  
                    hoja_cartera.write(row,14, monto_rendimiento_usd ,                        formato_decimal_hoja2)  
                    row += 1
                    subtotal_global_pyg += monto_rendimiento_pyg
                    subtotal_global_usd += monto_rendimiento_usd


            for movimiento in fondo.movimiento_fondo_ids:
                monto_movimiento_gs = 0
                monto_movimiento_usd = 0

                if is_usd:
                    monto_movimiento_usd = movimiento.monto
                    if self.cambio_utilizado:
                        monto_movimiento_gs = monto_movimiento_usd * self.cambio_utilizado
                    else:
                        monto_movimiento_gs = monto_movimiento_usd * fondo.cambio_utilizado
                else:
                    monto_movimiento_gs = movimiento.monto
                    if self.cambio_utilizado:
                        monto_movimiento_usd = monto_movimiento_gs/ self.cambio_utilizado
                    else:
                        try:
                            monto_movimiento_usd = monto_movimiento_gs / fondo.cambio_utilizado
                        except ZeroDivisionError:
                            monto_movimiento_usd = 0
                print("Movimiento", movimiento.tipo, movimiento.fecha)
                print(fondo.currency_id, is_usd, movimiento.monto)
                print("Monto antes", cruce_contable_valores[cuenta]['total_inversion'] )
                if movimiento.tipo == 'retiro':
                    cruce_contable_valores[cuenta]['total_inversion'] = cruce_contable_valores[cuenta]['total_inversion'] - monto_movimiento_gs
                else:
                    cruce_contable_valores[cuenta]['total_inversion']= cruce_contable_valores[cuenta]['total_inversion'] + monto_movimiento_gs
                print(monto_movimiento_gs)
                print("Monto despues", cruce_contable_valores[cuenta]['total_inversion'])

        ## Subtotales hoja 2 ##
        hoja_cartera.write(row,12, "Subtotales",                        numerico_total)  
        hoja_cartera.write(row,13, subtotal_global_pyg,                        formato_entero_hoja2)  
        hoja_cartera.write(row,14, subtotal_global_usd ,                        formato_decimal_hoja2)  


        ### FIN REGISTROS ###
        
        hoja_cartera.set_column('A:B', 40)
        hoja_cartera.set_column('C:D', 15)
        hoja_cartera.set_column('E:E', 35)
        hoja_cartera.set_column('F:J', 20)
        hoja_cartera.set_column('F:L', 35)


        ### Preparar Caratula - Hoja 1 ###
        headers = [
            "Cuenta","Denominación cuenta contable", "Moneda", "", "Suma de Importe Valorizado", "Suma de Valor actual en PYG"
        ]

        for col in range(0, 6):
            hoja_caratura.write(1, col, "", titulo)
            hoja_caratura.write(2, col, "", titulo)
            hoja_caratura.write(3, col, "", titulo)

        hoja_caratura.write_row(4, 0, headers, titulo_oscuro)

        row = 5
        # se itera el dic de las cuentas con sus valores inicializados en el anterior bucle
        for cuenta in cruce_contable_valores.keys():
            # _logger.info(f"Cuentas: {cuenta}")
            totales = 0
            if cruce_contable_valores[cuenta]['total_vencido'] > 0:
                #hoja_caratura.write(row, 1, cruce_contable_valores[cuenta]['moneda'], formato_entero)
                #hoja_caratura.write(row, 2, "Vencido", formato_entero)
                #hoja_caratura.write(row, 3, round(cruce_contable_valores[cuenta]['total_vencido'], 2),
                #                    formato_entero)
                totales += cruce_contable_valores[cuenta]['total_vencido']
                #row += 1
            if cruce_contable_valores[cuenta]['total_cobrado'] > 0:
                #hoja_caratura.write(row, 1, cruce_contable_valores[cuenta]['moneda'], formato_entero)
                #hoja_caratura.write(row, 2, "Cobrado", formato_entero)
                #hoja_caratura.write(row, 3, round(cruce_contable_valores[cuenta]['total_cobrado'], 2),
                #                    formato_entero)
                totales += cruce_contable_valores[cuenta]['total_cobrado']
                #row += 1
            if cruce_contable_valores[cuenta]['total_pendiente'] > 0:
                #hoja_caratura.write(row, 1, cruce_contable_valores[cuenta]['moneda'], formato_entero)
                #hoja_caratura.write(row, 2, "Pendiente", formato_entero)
                #hoja_caratura.write(row, 3, round(cruce_contable_valores[cuenta]['total_pendiente'], 2),
                #                    formato_entero)
                totales += cruce_contable_valores[cuenta]['total_pendiente']
                #row += 1
            if 'total_inversion' in cruce_contable_valores[cuenta].keys(): # los fondos entran aca
                #print(cuenta ,cruce_contable_valores[cuenta])
                #hoja_caratura.write(row, 1, cruce_contable_valores[cuenta]['moneda'], formato_entero)
                #hoja_caratura.write(row, 2, "Total Inversion", formato_entero)
                #hoja_caratura.write(row, 3, round(cruce_contable_valores[cuenta]['total_inversion'], 2),
                #                    formato_entero)
                totales += cruce_contable_valores[cuenta]['total_inversion']
                #row += 1

            if cruce_contable_valores[cuenta]['moneda'] == 'Dolares Americanos':
                importe_valorizado = totales / self.cambio_utilizado if self.cambio_utilizado else 0
            else:
                importe_valorizado = totales

            hoja_caratura.write(row, 0, cruce_contable_valores[cuenta]['code'] , titulo_oscuro2)
            hoja_caratura.write(row, 1,cuenta    , formato_entero)
            hoja_caratura.write(row, 2, cruce_contable_valores[cuenta]['moneda'], formato_entero)
            hoja_caratura.write(row, 3, '', formato_entero)
            hoja_caratura.write(row, 4, importe_valorizado, formato_entero)
            hoja_caratura.write(row, 5, totales, formato_entero)
            row+=1
            hoja_caratura.write(row, 0, "Subtotal", titulo_oscuro)
            hoja_caratura.write(row, 1, "", titulo_oscuro2)
            hoja_caratura.write(row, 2, "", titulo_oscuro2)
            hoja_caratura.write(row, 3, '', titulo_oscuro2)
            hoja_caratura.write(row, 4, importe_valorizado, formato_decimal_gris)
            hoja_caratura.write(row, 5, round(totales, 2), formato_entero_oscuro)

            row += 1
        
        ## Escribir sub totales en la caratula ##
        hoja_caratura.write(row, 4, subtotal_global_usd, formato_decimal_gris)
        hoja_caratura.write(row, 5, subtotal_global_pyg, formato_entero_oscuro)
        ## Escribir la cotizacion que se utilizo ##
        if self.cambio_utilizado:
            hoja_caratura.write(3, 4, 'Cotizacion', titulo)
            hoja_caratura.write(3, 5, self.cambio_utilizado, titulo)

        # seteaR un anchSo de las colunmas
        hoja_caratura.set_column('A:A', 10)
        hoja_caratura.set_column('B:B', 70)
        hoja_caratura.set_column('B:E', 20)
        hoja_caratura.set_column('E:F', 35)
        workbook.close()
        output.seek(0)
        # Guardar el archivo en el campo 'reporte_excel'
        self.reporte_excel = base64.b64encode(output.getvalue())
        self.reporte_nombre = f"Reporte_Devengamiento.xlsx"
        print(f"Guardar reporte: {guardar_reporte}")
        # entra aca cuando se le llama desde el boton de guardar

        if guardar_reporte:
            fecha_plazo_reporte = self.fecha_plazo if self.fecha_plazo else fields.Date.today()
            self.env['pbp.reporte_vencimientos'].create({
                'name': f"Reporte de Vencimientos {fecha_plazo_reporte.strftime('%d-%m-%Y')}",
                'fecha_inicio': self.fecha_inicio,
                'fecha_fin': self.fecha_fin,
                'fecha_plazo': fecha_plazo_reporte,
                'reporte_excel': self.reporte_excel,
                'state': 'prueba',
            })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/download/reporte_vencimientos/{self.id}', # controlador definido en controllers
            'target': 'self',
        }



