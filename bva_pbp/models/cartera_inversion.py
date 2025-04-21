import datetime
import calendar

from odoo import models, fields, api, exceptions
import io
import xlsxwriter
import base64
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
#generar_asientos_devengamiento
#crear_asiento_devengar

class CarteraInversion(models.Model):
    _name = 'pbp.cartera_inversion'
    _order = 'state, fecha_compra desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'id'

    reporte_excel = fields.Binary(string="Reporte Excel", readonly=True)
    reporte_nombre = fields.Char(string="Nombre del Archivo", readonly=True)


    emision = fields.Char(string='Emisión')
    serie = fields.Char(string="Serie", required=True)
    fecha_actual = fields.Date(string="Fecha")
    cambio_utilizado = fields.Float(string="Cotizacion")
    calificacion_riesgo = fields.Char(string='Calificación Riesgo')
    tasa_interes = fields.Float(string='Tasa Interés', digits=(7, 6))
    valor_actual_pyg = fields.Float(string='Valor Actual en PYG', digits=(17, 6), compute="compute_valor_final")
    valor_actual_usd = fields.Float(string='Valor Actual en USD', digits=(17, 6))
    amortizacion = fields.Float(string='Amortización', digits=(17, 6))
    estado_de_cupon = fields.Char(string='Estado de Cupón / Capital')
    comitente = fields.Integer()
    vencimiento_ids = fields.One2many("pbp.vencimiento_capital_interes", "registros", string="Vencimientos")
    capital = fields.Float(string="Capital")
    valor_calculado = fields.Float(compute='compute_valor_final', store=True, string='Total')
    incompleto = fields.Boolean(compute='compute_incompleto', store=True)


    fecha_compra = fields.Date(string='Fecha de Compra')
    importe_valorizado = fields.Float(digits=(17, 6), required=True)#corte
    valor_nominal = fields.Integer(string="Valor nominal")
    cantidad = fields.Integer(string="Cantidad de titulos")
    intereses = fields.Float(digits=(17, 6), string="Intereses", compute="compute_valor_final")#Tasa Nominal
    interes_diario = fields.Float(string="Interes Diario")
    tipo_pago = fields.Selection(
        selection=[
            ('trimestral', 'Trimestrales')
        ]
    )
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento', required=True)




    tipo = fields.Selection(
        selection=[
            ('intereses', 'Intereses'),
            ('capital', 'Capital'),
        ], required=True
    )
    grupo_id = fields.Many2one('pbp.grupo_cartera_inversion')
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
    state = fields.Selection(
        selection=[
            ('cobrado', 'Cobrado'),
            ('vencido_cobrado', 'Vencido/Cobrado'),
            ('activo', 'Activo'),
            ('cobrado_no_renovado', 'Cobrado | No renovado'),
            ('incumplimiento_provisionado', 'Incumplimiento | Provisionado'),
            ('reestructurado', 'Reestructurado'),
            ('vencido', 'Vencido | Renovado'),
            ('pendiente', 'Pendiente'),
            ('draft', 'Draft'),
            ('publicado', 'Publicado'),
        ],
        required=True,
        default='pendiente',
        string='Estado',
    )

    partner_id = fields.Many2one('res.partner', string='Emisor')
    casa_bolsa = fields.Many2one('res.partner', string='Casa de Bolsa')
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True)
    move_id = fields.Many2one('account.move', string="Asiento", copy=False)
    product_id = fields.Many2one('product.product', string='Producto')
    correo_enviado = fields.Boolean(string="Correo enviado", default=False, copy=False, tracking=True)
    mail_id = fields.Many2one('mail.mail', string="Correo", copy=False, tracking=True)
    voucher_id = fields.Many2one(
        'account.voucher',
        string="Voucher",
        ondelete="cascade"
    )
    ########### CAMPOS PARA ASIENTO DE PAGO INICIAL ##################
    inversion_account_id = fields.Many2one('account.account',string="Cuenta de Inversión",
        tracking=True)
    banco_account_id = fields.Many2one('account.account',string="Cuenta de Banco",
        tracking=True)
    inversion_journal_id = fields.Many2one('account.journal',string="Diario de inversión",
        tracking=True)
    ########### CAMPOS PARA ASIENTO INICIAL A DEVENGAR ################
    initial_credit_account_id = fields.Many2one('account.account', string='Cuenta acreedora inicial a devengar CP',
        tracking=True)
    initial_credit_largo_plazo_account_id = fields.Many2one('account.account', string='Cuenta acreedora inicial a devengar LP',
        tracking=True)
    initial_debit_account_id = fields.Many2one('account.account', string='Cuenta deudora inicial a devengar CP',
        tracking=True)
    initial_debit_account_id_lp = fields.Many2one('account.account', string='Cuenta deudora inicial a devengar LP',
                                               tracking=True)
    initial_journal_id = fields.Many2one('account.journal',string="Diario de asiento a devengar",
        tracking=True)
    initial_move_ids = fields.One2many(
        'account.move',
        'initial_cartera_id',  # Campo inverso en `account.move`
        string="Asientos Iniciales",
        copy=False
    )
    fecha_inicio_devengamiento = fields.Date(string="Fecha de inicio de devengamiento",
        tracking=True)
    fecha_final_devengamiento = fields.Date(string="Fecha final de devengamiento",
        tracking=True)
    cant_meses_devengamiento = fields.Integer(
        string="Cantidad de meses de devengamiento",
        compute="_compute_cant_meses_devengamiento",
        store=True
    )
    intereses_corto_plazo = fields.Float(
        string="Intereses Corto Plazo",
        compute="_compute_intereses_devengamiento",
        store=True
    )

    intereses_largo_plazo = fields.Float(
        string="Intereses Largo Plazo",
        compute="_compute_intereses_devengamiento",
        store=True
    )
    initial_move_count = fields.Integer(
        string="Cantidad de Asientos Iniciales",
        compute="_compute_initial_move_count",
    )
    ########### CAMPOS PARA DEVENGAMIENTO ############################
    credit_account_id = fields.Many2one('account.account', string='Cuenta de ingresos',
        tracking=True)
    debit_account_id = fields.Many2one('account.account', string='Cuenta de devengamiento',
        tracking=True)
    move_ids = fields.One2many(
        'account.move',
        'cartera_id',  # Campo inverso en `account.move`
        string="Asientos contables de devengamiento"
    )
    move_count = fields.Integer(
        string="Cantidad de Asientos Contables",
        compute="_compute_move_count",
        store=True
    )
    plazo_pago_intereses = fields.Integer(string="Tramo en días para pago de intereses",required=True,
        tracking=True)
    tipo_devengamiento = fields.Selection(
        selection=[
            ('fijo', 'Fijo'),
            ('dias', 'Días'),
        ],
        default='fijo',
        string='Tipo de devengamiento',
        required=True,
        tracking=True
    )
    tipo_mercado = fields.Selection(
        selection=[
            ('primario', 'Primario'),
            ('secundario', 'Secundario'),
        ],
        default="primario",
        required=True,
        tracking=True

    )

    def generar_asientos_masivamente(self):
        # generar_asientos_devengamiento
        # crear_asiento_devengar

        regs_cartera = self.env["pbp.cartera_inversion"].search([('instrumento', 'not in', ('bonos_del_tesoro', 'fondos'))])
        for cartera in regs_cartera:
            try:
                cartera.generar_asientos_devengamiento()
                cartera.crear_asiento_devengar()
            except:
                pass





    @api.depends('move_ids')
    def _compute_move_count(self):
        """Cuenta los registros relacionados en move_ids."""
        for record in self:
            record.move_count = len(record.move_ids)



    @api.depends('initial_move_ids')
    def _compute_initial_move_count(self):
        """Cuenta los registros relacionados en initial_move_ids."""
        for record in self:
            record.initial_move_count = len(record.initial_move_ids)

    def action_view_moves(self):
        """Abre una vista de los asientos contables asociados a move_ids."""
        self.ensure_one()
        if not self.move_ids:
            raise exceptions.UserError("No hay asientos contables asociados a este registro.")

        tree_view_id = self.env.ref('account.view_move_tree').id
        form_view_id = self.env.ref('account.view_move_form').id


        return {
            'type': 'ir.actions.act_window',
            'name': 'Asientos Mensuales de Devengamiento',
            'res_model': 'account.move',
            'view_mode': 'tree,form',  # Vista en lista y formulario
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],  # Prioridad tree, alternativo form
            'domain': [('id', 'in', self.move_ids.ids)],  # Filtrar los asientos relacionados
            'context': self.env.context,
        }

    def calcular_dias(self, fecha_inicio, fecha_fin):
        # Convertir las fechas de string a objeto datetime
        formato = "%Y-%m-%d"
        fecha_inicio = datetime.strptime(fecha_inicio, formato)# + timedelta(days=1)  # Sumar 1 día
        #fecha_inicio = fecha_inicio#datetime.strptime(fecha_inicio, formato) + timedelta(days=1)  # Sumar 1 día

        fecha_fin = datetime.strptime(fecha_fin, formato)

        # Calcular la diferencia en días
        diferencia = (fecha_fin - fecha_inicio).days
        print("Diferencia", diferencia)
        return diferencia

    def generar_reporte_excel(self):
        """Genera un reporte ultra detallado en Excel con todos los cálculos explicados paso a paso."""
        for record in self:
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            sheet = workbook.add_worksheet("Reporte Devengamiento")

            # Formatos
            bold = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
            currency_format = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
            center_format = workbook.add_format({'align': 'center', 'border': 1})
            wrap_format = workbook.add_format({'text_wrap': True, 'border': 1, 'align': 'left'})

            # Definir encabezados con explicaciones
            headers = [
                "Mes", "Fecha Inicio", "Fecha Fin", "Días Totales Devengamiento",
                "Días Devengados en el Mes", "Fórmula Días Devengados",
                "Interés Total", "Días Totales", "Interés Diario", "Fórmula Interés Diario",
                "Monto Devengado en el Mes", "Fórmula Monto Devengado",
                "Cuenta Débito", "Cuenta Crédito"
            ]
            sheet.write_row(0, 0, headers, bold)

            # Variables base
            fecha_actual = record.fecha_inicio_devengamiento
            fecha_fin = record.fecha_final_devengamiento
            dias_totales_devengamiento = self.calcular_dias(str(fecha_actual), str(fecha_fin))
            print("Calculo", dias_totales_devengamiento)
            row = 1

            # Calcular interés diario si aplica
            if record.tipo_devengamiento == 'dias':
                interes_diario = record.intereses / dias_totales_devengamiento
                formula_interes_diario = f"Interés Diario = {record.intereses} / {dias_totales_devengamiento}"
            else:
                interes_diario = None  # No se usa en devengamiento fijo
                formula_interes_diario = "N/A (Devengamiento Fijo)"
            fecha_fin += relativedelta(months=1)
            # Generar filas con cálculos detallados
            while fecha_actual <= fecha_fin:
                print(f"Inicia Bucle - Fecha Actual: {fecha_actual} - Fecha Fin {fecha_fin}")
                if record.tipo_devengamiento == 'dias':
                    # 🔹 Obtener el primer y último día del mes
                    if fecha_actual == record.fecha_inicio_devengamiento:
                        fecha_inicio_mes = fecha_actual + timedelta(days=1)
                    else:
                        fecha_inicio_mes = max(fecha_actual.replace(day=1), record.fecha_inicio_devengamiento)


                    fecha_fin_mes = min(
                        fecha_actual.replace(day=calendar.monthrange(fecha_actual.year, fecha_actual.month)[1]),
                        record.fecha_final_devengamiento
                    )
                    #if fecha_fin_mes == record.fecha_final_devengamiento:
                        #fecha_fin_mes = record.fecha_final_devengamiento - timedelta(days=1)
                    # 🔹 Calcular días devengados en el mes
                    dias_devengados = (fecha_fin_mes - fecha_inicio_mes).days + 1
                    monto_mensual = interes_diario * dias_devengados

                    # 🔹 Explicaciones detalladas
                    formula_dias_devengados = (
                        f"MIN({fecha_fin_mes.strftime('%d-%m-%Y')}, {record.fecha_final_devengamiento.strftime('%d-%m-%Y')}) - "
                        f"MAX({fecha_inicio_mes.strftime('%d-%m-%Y')}, {record.fecha_inicio_devengamiento.strftime('%d-%m-%Y')}) + 1"
                    )
                    formula_monto_devengado = f"{interes_diario:.6f} * {dias_devengados}"

                else:
                    dias_devengados = "Fijo"
                    monto_mensual = record.intereses / record.cant_meses_devengamiento
                    formula_monto_devengado = f"{record.intereses} / {record.cant_meses_devengamiento}"
                    formula_dias_devengados = "Fijo (Se devenga un monto fijo mensual)"

                if monto_mensual < 0:
                    fecha_actual += relativedelta(months=1)
                    continue
                # Agregar fila con cálculos explicados
                sheet.write(row, 0, fecha_actual.strftime('%B %Y'), center_format)
                sheet.write(row, 1, fecha_inicio_mes.strftime('%d-%m-%Y'), center_format)
                sheet.write(row, 2, fecha_fin_mes.strftime('%d-%m-%Y'), center_format)
                sheet.write(row, 3, dias_totales_devengamiento, center_format)
                sheet.write(row, 4, dias_devengados, center_format)
                sheet.write(row, 5, formula_dias_devengados, wrap_format)
                sheet.write(row, 6, record.intereses, currency_format)
                sheet.write(row, 7, dias_totales_devengamiento, center_format)
                sheet.write(row, 8, interes_diario if interes_diario else "N/A", currency_format)
                sheet.write(row, 9, formula_interes_diario, wrap_format)
                sheet.write(row, 10, monto_mensual, currency_format)
                sheet.write(row, 11, formula_monto_devengado, wrap_format)
                sheet.write(row, 12, record.debit_account_id.display_name, center_format)
                sheet.write(row, 13, record.credit_account_id.display_name, center_format)

                # Avanzar al siguiente mes
                fecha_actual += relativedelta(months=1)
                print(
                    f"Bucle Fin Se aniade un mes mas a fecha actual- Fecha Actual: {fecha_actual} - Fecha Fin {fecha_fin}")


                row += 1
            print("DIas Devengados ", dias_totales_devengamiento)
            workbook.close()
            output.seek(0)

            # Guardar el archivo en el campo `reporte_excel`
            record.reporte_excel = base64.b64encode(output.getvalue())
            record.reporte_nombre = f"Reporte_Devengamiento_{record.id}.xlsx"

            return {
                'type': 'ir.actions.act_url',
                'url': f'/download/reporte_devengamiento/{record.id}',
                'target': 'self',
            }
    ### hacer mas legible dps
    def generar_asientos_devengamiento(self):
        """Genera los asientos mensuales de devengamiento con base en el tipo seleccionado (fijo o días)."""
        for record in self:
            if not record.credit_account_id or not record.debit_account_id:
                raise exceptions.UserError("Debe configurar las cuentas de ingresos y devengamiento.")
            if not record.fecha_inicio_devengamiento or not record.fecha_final_devengamiento:
                raise exceptions.UserError("Debe configurar las fechas de inicio y fin del devengamiento.")
            if record.cant_meses_devengamiento <= 0:
                raise exceptions.UserError("La cantidad de meses de devengamiento debe ser mayor a 0.")
            total_dias_suma = 0
            dias_devengados_suma = 0
            total_suma_montos = 0
            # Fecha inicial y final
            fecha_actual = record.fecha_inicio_devengamiento
            fecha_fin = record.fecha_final_devengamiento
            print("Total Intereses: ", record.intereses)
            # Calculo del interes diario, solo cuando se selecciona dias
            if record.tipo_devengamiento == 'dias':
                dias_totales = (fecha_fin - fecha_actual).days + 1
                dias_totales = self.calcular_dias(str(fecha_actual), str(fecha_fin))
                print("Calculo", dias_totales)
                #print("fecha_fin", fecha_fin, "fecha_actual", fecha_actual)
                #print("c", (fecha_fin - fecha_actual).days +1)
                #print("Dias Totales Mes Funcion",dias_totales )
                total_dias_suma += dias_totales
                interes_diario = record.intereses / dias_totales

            # Lista para almacenar los IDs de los asientos creados
            asientos_creados = []
            cont_mes = 1

            # Generar los asientos mensuales o diarios según el tipo
            fecha_fin += relativedelta(months=1)
            # fecha_actual = fecha_actual + relativedelta(day=1)
            while fecha_actual <= fecha_fin:
                print(f"Inicia Bucle - Fecha Actual: {fecha_actual} - Fecha Fin {fecha_fin}")
                #print(f"Fecha Actual: {fecha_actual} - {fecha_fin}")
                # calcula los dias del mes actual
                if record.tipo_devengamiento == 'dias':
                    dias_en_mes = calendar.monthrange(fecha_actual.year, fecha_actual.month)[1]
                    if fecha_actual == record.fecha_inicio_devengamiento:
                        fecha_inicio_mes = fecha_actual + timedelta(days=1)
                    else:
                        fecha_inicio_mes = max(fecha_actual.replace(day=1), record.fecha_inicio_devengamiento)


                    fecha_fin_mes = min(
                        fecha_actual.replace(day=calendar.monthrange(fecha_actual.year, fecha_actual.month)[1]),
                        record.fecha_final_devengamiento)

                    #if fecha_fin_mes == record.fecha_final_devengamiento:
                        #fecha_fin_mes = record.fecha_final_devengamiento - timedelta(days=1)
                    dias_devengados = (fecha_fin_mes - fecha_inicio_mes).days + 1
                    dias_devengados_suma += dias_devengados
                    #print(f"{cont_mes} Dias en mes", dias_devengados)
                    cont_mes += 1
                    #print(f"{fecha_actual}- {fecha_actual.year} - {fecha_actual.month}")
                    monto_mensual = interes_diario * dias_devengados
                    #print(f"{fecha_inicio_mes} - {fecha_fin_mes} - {dias_devengados} - {dias_devengados_suma} Monto Mensual: {monto_mensual}")
                    total_suma_montos += monto_mensual
                    print(f"Monto Mensual: {monto_mensual}")
                else:  # Caso fijo
                    monto_mensual = record.intereses / record.cant_meses_devengamiento
                    total_suma_montos += monto_mensual
                    print(f"Monto Mensual: {monto_mensual}")
                if monto_mensual < 0:
                    fecha_actual += relativedelta(months=1)
                    print(
                        f"Bucle Fin Se aniade un mes mas a fecha actual- Fecha Actual: {fecha_actual} - Fecha Fin {fecha_fin}")
                    continue

                # Formatear la referencia con el mes y la serie
                referencia = f"Asiento Devengamiento - {fecha_actual.strftime('%B %Y')} - {record.serie or 'N/A'}"
                #print("Referencia", referencia)
                # Crear las lineas contables
                moneda_alternativa = monto_mensual / record.cambio_utilizado if record.currency_id.id == 2 else monto_mensual
                move_lines = [
                    {
                        'account_id': record.debit_account_id.id,
                        'debit': monto_mensual,
                        'credit': 0.0,
                        'name': referencia,
                        'currency_id': record.currency_id.id,
                        'amount_currency': moneda_alternativa,
                        'currency_rate': record.cambio_utilizado
                    },
                    {
                        'account_id': record.credit_account_id.id,
                        'debit': 0.0,
                        'credit': monto_mensual,
                        'name': referencia,
                        'amount_currency':moneda_alternativa * (-1),
                        'currency_id': record.currency_id.id,
                        'currency_rate': record.cambio_utilizado
                    },
                ]
                #print(move_lines)
                # Crear el asiento
                move_vals = {
                    'journal_id': record.initial_journal_id.id,
                    'date': fecha_actual.replace(day=calendar.monthrange(fecha_actual.year, fecha_actual.month)[1]),
                    'line_ids': [(0, 0, line) for line in move_lines],
                    'ref': referencia,
                    'cartera_id': record.id,  # Relación con la cartera de inversión
                    # 'currency_rate': record.cambio_utilizado,
                    'currency_id': record.currency_id.id
                }
                move = self.env['account.move'].create(move_vals)

                # Agregar el ID del asiento creado a la lista
                asientos_creados.append(move.id)

                # Avanzar al siguiente mes
                fecha_actual += relativedelta(months=1)
                print(f"Bucle Fin Se aniade un mes mas a fecha actual- Fecha Actual: {fecha_actual} - Fecha Fin {fecha_fin}")
                #print("Fecha Actual", fecha_actual, "Fecha Fin",fecha_fin,fecha_actual <= fecha_fin)

            # Asociar los asientos creados al campo move_ids
            record.move_ids = [(6, 0, asientos_creados)]

            # Mensaje en el chatter
            record.message_post(
                body=f"Se han generado {len(asientos_creados)} asientos mensuales de devengamiento desde {record.fecha_inicio_devengamiento} hasta {record.fecha_final_devengamiento}."
            )
            #print("Dias totales tomados", dias_totales)
            print("Monto Mensual", total_suma_montos)
            print("Dias Devengados suma", dias_devengados_suma)

    @api.depends('fecha_inicio_devengamiento', 'fecha_final_devengamiento', 'intereses')
    def _compute_intereses_devengamiento(self):
        for record in self:
            # Inicializar valores por defecto
            record.intereses_corto_plazo = 0.0
            record.intereses_largo_plazo = 0.0
            dias_corto_plazo = 0

            print(
                f"Se calcula en el rango de fecha \n{record.fecha_inicio_devengamiento} - \n{record.fecha_final_devengamiento}")

            # Validar que las fechas y el valor de intereses esten definidos
            if record.fecha_inicio_devengamiento and record.fecha_final_devengamiento and record.intereses > 0:
                inicio = record.fecha_inicio_devengamiento
                fin = record.fecha_final_devengamiento
                hoy = fields.Date.today()

                # Total dias del devengamiento
                total_dias = (fin - inicio).days
                print(f"Total de días de devengamiento: {total_dias}")

                if total_dias <= 0:
                    raise exceptions.UserError("Las fechas de inicio y fin de devengamiento no son válidas.")

                # Calculo de días proporcionales del primer mes
                dias_en_mes_inicio = (inicio.replace(day=1) + relativedelta(months=1, days=-1)).day
                dias_primer_mes = dias_en_mes_inicio - inicio.day

                # Cálculo de días proporcionales del último mes
                dias_ultimo_mes = fin.day
                dias_en_mes_fin = (fin.replace(day=1) + relativedelta(months=1, days=-1)).day

                # Dias intermedios completos
                dias_intermedios = total_dias - dias_primer_mes - dias_ultimo_mes

                # Calcular intereses diarios
                interes_diario = record.intereses / total_dias
                print(f"Interés diario: {interes_diario}")
                print("Dias primer mes", dias_primer_mes)
                # Calcular intereses prorrateados
                intereses_primer_mes = interes_diario * dias_primer_mes
                intereses_ultimo_mes = interes_diario * dias_ultimo_mes
                intereses_intermedios = interes_diario * dias_intermedios


                #fin de ano actual
                fin_ano_actual = hoy.replace(month=12, day=31)

                if fin <= fin_ano_actual:  # Todo dentro de corto plazo
                    record.intereses_corto_plazo = record.intereses
                    record.intereses_largo_plazo = 0.0
                else:  # Hay parte en corto y parte en largo plazo
                    dias_corto_plazo = (fin_ano_actual - inicio).days + 1
                    if dias_corto_plazo < 0:
                        dias_corto_plazo = 0  # No puede haber dias negativos

                    record.intereses_corto_plazo = interes_diario * dias_corto_plazo
                    record.intereses_largo_plazo = max(0,
                                                       record.intereses - record.intereses_corto_plazo)  # Evitar negativos

                # # Determinar corto y largo plazo
                # if inicio <= hoy <= fin:
                #     dias_corto_plazo = (hoy - inicio).days + 1
                #     print(f"Hoy {hoy} - {inicio}", dias_corto_plazo)
                #     fecha_inicio = record.fecha_inicio_devengamiento
                #     fin_ano_actual = hoy.replace(month=12, day=31)
                #     dias_corto_plazo = (fin_ano_actual - fecha_inicio).days
                #     print(f"{fin_ano_actual} - {fecha_inicio}")
                #     print("Dias Corto Plazo: ", dias_corto_plazo)
                #     record.intereses_corto_plazo = interes_diario * dias_corto_plazo
                #     record.intereses_largo_plazo = record.intereses - record.intereses_corto_plazo
                # else:
                #     print("Dias Corto Plazo: ", dias_corto_plazo)
                #     record.intereses_corto_plazo = intereses_primer_mes + intereses_intermedios
                #     record.intereses_largo_plazo = intereses_ultimo_mes

                print(f"Intereses primer mes: {intereses_primer_mes}")
                print(f"Intereses intermedios: {intereses_intermedios}")
                print(f"Intereses último mes: {intereses_ultimo_mes}")
                print(f"Intereses corto plazo: {record.intereses_corto_plazo}")
                print(f"Intereses largo plazo: {record.intereses_largo_plazo}")

    @api.depends('fecha_inicio_devengamiento', 'fecha_final_devengamiento')
    def _compute_cant_meses_devengamiento(self):
        for record in self:
            if record.fecha_inicio_devengamiento and record.fecha_final_devengamiento:
                inicio = record.fecha_inicio_devengamiento
                fin = record.fecha_final_devengamiento

                # Diass del mes inicial y final
                dias_en_mes_inicio = (inicio.replace(day=1) + relativedelta(months=1, days=-1)).day
                print("Dias en mes inicio")
                print(dias_en_mes_inicio)
                dias_primer_mes = dias_en_mes_inicio - inicio.day + 1
                print(dias_primer_mes)
                dias_ultimo_mes = fin.day
                print(dias_ultimo_mes)
                # Total dias en el primer y ultimo mes
                total_dias_primer_mes = dias_en_mes_inicio
                total_dias_ultimo_mes = (fin.replace(day=1) + relativedelta(months=1, days=-1)).day

                # Meses completos intermedios
                meses_completos = max(0, (fin.year - inicio.year) * 12 + fin.month - inicio.month - 1)

                # Ajustar el total de meses con los días proporcionales del primer y ultimo mes
                record.cant_meses_devengamiento = meses_completos + (dias_primer_mes / total_dias_primer_mes) + (
                            dias_ultimo_mes / total_dias_ultimo_mes)
            else:
                record.cant_meses_devengamiento = 0

    def calcular_intereses_proporcionales(self, inicio, fin, intereses_totales):
        """Calcula los intereses proporcionales para el primer mes, meses completos, y último mes."""
        # Dias del primer mes
        dias_en_mes_inicio = (inicio.replace(day=1) + relativedelta(months=1, days=-1)).day
        dias_primer_mes = dias_en_mes_inicio - inicio.day + 1

        # Dias del último mes
        dias_ultimo_mes = fin.day
        dias_en_mes_fin = (fin.replace(day=1) + relativedelta(months=1, days=-1)).day

        # Meses completos intermedios
        meses_completos = max(0, (fin.year - inicio.year) * 12 + fin.month - inicio.month - 1)

        # Días totales del devengamiento
        dias_totales = (fin - inicio).days + 1

        # Intereses por cada parte
        intereses_primer_mes = intereses_totales * (dias_primer_mes / dias_totales)
        intereses_ultimo_mes = intereses_totales * (dias_ultimo_mes / dias_totales)
        intereses_meses_completos = intereses_totales - (intereses_primer_mes + intereses_ultimo_mes)

        return intereses_primer_mes, intereses_meses_completos, intereses_ultimo_mes


    def crear_asiento_devengar(self):
        """Crea dos asientos contables: uno para corto plazo y otro para largo plazo."""
        for record in self:
            # Validaciones iniciales
            if not record.initial_credit_account_id or not record.initial_credit_largo_plazo_account_id \
                    or not record.initial_debit_account_id or not record.initial_journal_id:
                raise exceptions.UserError(
                    "Debe completar las cuentas iniciales y el diario de asiento a devengar para crear los asientos contables."
                )
            if record.intereses <= 0:
                raise exceptions.UserError(
                    "El valor de 'Intereses' debe ser mayor a 0 para crear los asientos contables.")

            if record.fecha_inicio_devengamiento > record.fecha_final_devengamiento:
                raise exceptions.UserError(
                    "La fecha de inicio de devengamiento no puede ser posterior a la fecha final.")

            # Calcular los intereses proporcionales
            intereses_primer_mes, intereses_meses_completos, intereses_ultimo_mes = self.calcular_intereses_proporcionales(
                record.fecha_inicio_devengamiento,
                record.fecha_final_devengamiento,
                record.intereses
            )
            print("Intereses primer mes")
            print(intereses_primer_mes)
            print("Intereses Completos")
            print(intereses_meses_completos)
            print("Intereses Ultimi mes")
            print(intereses_ultimo_mes)
            # Calcular corto y largo plazo
            intereses_corto_plazo = intereses_primer_mes + intereses_meses_completos
            intereses_largo_plazo = intereses_ultimo_mes

            # Crear asiento para corto plazo
            move_lines_corto = [
                {
                    'account_id': record.initial_debit_account_id.id,
                    'debit': record.intereses_corto_plazo,
                    'credit': 0.0,
                    'name': f"Asiento Devengar CP - {record.serie or 'N/A'}",
                },
                {
                    'account_id': record.initial_credit_account_id.id,
                    'debit': 0.0,
                    'credit': record.intereses_corto_plazo,
                    'name': f"Asiento Devengar CP - {record.serie or 'N/A'}",
                },
            ]
            move_vals_corto = {
                'journal_id': record.initial_journal_id.id,
                'date': fields.Date.context_today(self),
                'line_ids': [(0, 0, line) for line in move_lines_corto],
                'ref': f"Asiento Devengar CP - {record.serie or 'N/A'}",
                'initial_cartera_id': record.id
            }
            move_corto = self.env['account.move'].create(move_vals_corto)
            #validacion para que no genere asiento en cero o negativo
            if record.intereses_largo_plazo > 0:
                # Crear asiento para largo plazo
                move_lines_largo = [
                    {
                        'account_id': record.initial_debit_account_id_lp    .id,
                        'debit': record.intereses_largo_plazo,
                        'credit': 0.0,
                        'name': f"Asiento Devengar LP - {record.serie or 'N/A'}",
                    },
                    {
                        'account_id': record.initial_credit_largo_plazo_account_id.id,
                        'debit': 0.0,
                        'credit': record.intereses_largo_plazo,
                        'name': f"Asiento Devengar LP - {record.serie or 'N/A'}",
                    },
                ]
                move_vals_largo = {
                    'journal_id': record.initial_journal_id.id,
                    'date': fields.Date.context_today(self),
                    'line_ids': [(0, 0, line) for line in move_lines_largo],
                    'ref': f"Asiento Devengar LP - {record.serie or 'N/A'}",
                    'initial_cartera_id': record.id
                }
                move_largo = self.env['account.move'].create(move_vals_largo)
                record.message_post(
                    body=f"Se han creado los asientos contables para devengar: {move_corto.name} (CP) y {move_largo.name} (LP)."
                )
            else:
                record.message_post(
                    body=f"Se han creado los asientos contables para devengar: {move_corto.name} (CP)."
                )



    def action_view_initial_moves(self):
        """Abre una vista de los asientos iniciales asociados."""
        self.ensure_one()  # Asegurarse de que haya un solo registro activo
        if not self.initial_move_ids:
            raise exceptions.UserError("No hay asientos iniciales asociados a este registro.")

        tree_view_id = self.env.ref('account.view_move_tree').id
        form_view_id = self.env.ref('account.view_move_form').id


        return {
            'type': 'ir.actions.act_window',
            'name': 'Asientos Iniciales a Devengar',
            'res_model': 'account.move',
            'view_mode': 'tree,form',  # Vista en lista y formulario
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],  # Prioridad tree, alternativo form
            'domain': [('id', 'in', self.initial_move_ids.ids)],  # Filtrar los asientos relacionados
            'context': self.env.context,
        }

    def action_view_voucher(self):
        """Abre la vista del voucher asociado."""
        self.ensure_one()
        if not self.voucher_id:
            raise exceptions.UserError("No hay un voucher asociado a este registro.")


        return {
            'type': 'ir.actions.act_window',
            'name': 'Voucher Asociado',
            'res_model': 'account.voucher',
            'view_mode': 'form',
            'res_id': self.voucher_id.id,
            'target': 'current',
            'context': self.env.context,
        }

    def crear_voucher(self):
        for record in self:
            # Validaciones previas
            if not record.inversion_journal_id:
                raise exceptions.UserError("Por favor, asegúrese de que el campo 'Cuenta de Inversión' esté completo.")
            if not record.banco_account_id:
                raise exceptions.UserError("Por favor, asegúrese de que el campo 'Cuenta de Banco' esté completo.")
            if not record.inversion_journal_id:
                raise exceptions.UserError("Por favor, asegúrese de que el campo 'Diario de inversión' esté completo.")

            # Crear la línea para el voucher
            voucher_line_vals = {
                'account_id': record.inversion_account_id.id,  # Cuenta de inversión
                'name': record.serie or "N/A",  # Referencia o serie
                'quantity': 1,  # Cantidad fija
                'price_unit': record.capital,  # Precio unitario
            }

            # Crear el voucher
            voucher_vals = {
                'voucher_type' : 'purchase',
                'partner_id': record.partner_id.id,  # Emisor
                'date': date.today(),  # Fecha actual
                'journal_id': record.inversion_journal_id.id,  # Diario de inversión
                'account_id': record.banco_account_id.id,  # Cuenta de banco
                'line_ids': [(0, 0, voucher_line_vals)],  # Añadir línea
                'state': 'draft',  # Estado borrador
                'name': f"Voucher Generado - {record.serie or 'N/A'}",  # Descripción del voucher
            }
            voucher = self.env['account.voucher'].create(voucher_vals)

            # Asociar el voucher generado con el registro actual
            record.voucher_id = voucher.id
            record.message_post(body=f"Se ha creado un nuevo pago inicial por la inversión: {voucher.name}")




    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for val in vals_list:
            if val['importe_valorizado'] <= 0:
                raise exceptions.UserError("No se puede crear el registro. El Importe valorizado debe ser mayor a 0")
        recs = super(CarteraInversion, self).create(vals_list)
        """for r in recs:
            if r.initial_credit_account_id and r.initial_debit_account_id:
                r.generarAsientoInicial()"""
        return recs

    def generarAsientoInicial(self):
        for cartera in self:
            liquidity_balance = cartera.importe_valorizado
            line_ids = []
            debit_line = {
                'debit': liquidity_balance,
                'credit': 0.0,
                'account_id': cartera.initial_debit_account_id.id,
                'partner_id': cartera.casa_bolsa.id,
                'currency_id': cartera.currency_id.id,
                'amount_currency': liquidity_balance,
            }
            line_ids.append((0, 0, debit_line))

            credit_line = {
                'credit': liquidity_balance,
                'debit': 0.0,
                'account_id': cartera.initial_credit_account_id.id,
                'partner_id': cartera.casa_bolsa.id,
                'currency_id': cartera.currency_id.id,
                'amount_currency': -liquidity_balance,
            }
            line_ids.append((0, 0, credit_line))
            move = {
                'ref': cartera.serie,
                'date': date.today(),
                'currency_id': cartera.currency_id.id,
                'move_type': 'entry',
            }
            move = self.env['account.move'].with_context(check_move_validity=False).create([move])
            move.write({'line_ids': line_ids})
            move.action_post()
            cartera.write({'initial_move_id': move.id})
    #2
    @api.onchange("cambio_utilizado")
    def _onchange_cambio(self):
        for record in self:
            print("Moneda", record.currency_id.id)
            record.compute_incompleto()

    #cambio_utilizado , importe_valorizado, valor_actual_pyg, valor_actula_usd, intereses, valor_calculado
    @api.depends('cambio_utilizado', 'importe_valorizado', 'valor_actual_pyg', "intereses", "valor_calculado")
    def compute_valor_final(self):
        for cartera in self:

            # setea Valor actual en pyg
            if (cartera.currency_id.id ==  2) and cartera.cambio_utilizado:# si es dolar y se seteo la cotizacion
                cartera.valor_actual_pyg = cartera.importe_valorizado * cartera.cambio_utilizado
            else:
                cartera.valor_actual_pyg = cartera.importe_valorizado

            #sumar intereses por vencimientos
            total_intereses = 0
            for venc in cartera.vencimiento_ids:
                if venc.amortizacion == 'vtoInt':
                    total_intereses += venc.total
            if cartera.currency_id.id == 2:# si es dolar
                total_intereses = total_intereses * cartera.cambio_utilizado

            # setea intereses
            cartera.intereses = total_intereses
            # setea total
            cartera.valor_calculado = cartera.intereses + cartera.valor_actual_pyg



    @api.depends('valor_calculado', 'debit_account_id', 'credit_account_id', 'casa_bolsa', 'currency_id', 'serie')
    def compute_incompleto(self):
        for cartera in self:
            if not (
                    cartera.serie and
                    cartera.casa_bolsa and
                    cartera.debit_account_id and
                    cartera.credit_account_id and
                    cartera.casa_bolsa and
                    cartera.currency_id
            ):
                cartera.incompleto = True
            else:
                cartera.incompleto = False

    @api.model
    def get_last_date_of_month(self, year, month):
        if month == 12:
            last_date = datetime(year, month, 31)
        else:
            last_date = datetime(year, month + 1, 1) + timedelta(days=-1)

        return last_date.strftime("%Y-%m-%d")

    @api.onchange('fecha_vencimiento')
    def onchangeFechaVencimiento(self):
        for i in self:
            if i.fecha_vencimiento:
                i.fecha_actual = i.get_last_date_of_month(i.fecha_vencimiento.year, i.fecha_vencimiento.month)
            else:
                i.fecha_actual = False

    """@api.onchange('tipo', 'instrumento', 'fecha_vencimiento', 'currency_id')
    def set_credit_debit_accounts(self):
        for cartera in self:
            credit_accounts = self.env['account.account'].search([
                ('cartera_acreedor_deudor', '=', 'acreedor'),
                ('cartera_tipo', '=', cartera.tipo),
            ])
            cartera.credit_account_id = credit_accounts[0] if credit_accounts else False

            vencimiento = False
            ten_years = date.today().year + 10
            if cartera.fecha_vencimiento and cartera.fecha_vencimiento.year > ten_years:
                vencimiento = 'largo_plazo'
            elif cartera.fecha_vencimiento:
                vencimiento = 'corto_plazo'

            debit_accounts = self.env['account.account'].search([('cartera_acreedor_deudor', '=', 'deudor')]).filtered(lambda account:
                (account.cartera_vencimiento == vencimiento or not account.cartera_vencimiento) and
                (account.cartera_instrumento == cartera.instrumento or not account.cartera_instrumento) and
                (account.cartera_tipo == cartera.tipo or not account.cartera_tipo) and
                (account.cartera_currency_id == cartera.currency_id or not account.cartera_currency_id)
            )
            cartera.debit_account_id = debit_accounts[0] if debit_accounts else False"""

    def marcar_como_inactivo(self):
        self.state = 'inactivo'
        dialog = self.env['pbp.dialog.box'].sudo().search([])[-1]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Message',
            'res_model': 'pbp.dialog.box',
            'view_mode': 'form',
            'target': 'new',
            'res_id': dialog.id
        }



    @api.model
    def generarAsientosVencimiento(self):
        fecha_actual = date.today()
        carteras_vencidas = self.env['pbp.cartera_inversion'].search([('fecha_vencimiento', '=', fecha_actual),
                                                                      ('credit_account_id', '!=', False),
                                                                      ('debit_account_id', '!=', False),
                                                                      ('move_id', '=', False)])
        if carteras_vencidas:
            carteras = carteras_vencidas.read((set(self.env['pbp.cartera_inversion']._fields)))
            carteras = [cartera for cartera in carteras]

            carteras_vencidas.mapped('move_id').action_post()


class GrupoCarteraInversion(models.Model):
    _name = 'pbp.grupo_cartera_inversion'
    _rec_name = 'nombre'

    nombre = fields.Char(required=True)
