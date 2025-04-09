# -*- coding: UTF-8 -*-

from odoo import fields, api, models
from odoo.exceptions import ValidationError
from odoo.tools import float_round
import time
from datetime import datetime, date, time, timedelta
import re
import logging

_logger = logging.getLogger(__name__)


class ReciboTalonario(models.Model):
    _name = 'account.recibo.talonario'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(string="Nombre del Talonario")
    usuario_talonario_ids = fields.Many2many('res.users', 'usuario_talonario_recibo_id_rel', 'user_id', 'talonario_id',
                                             string='Usuarios', ondelete='cascade')
    desde = fields.Integer(string="Primer número", help='Ingresar el primer numero del talonario de recibo')
    hasta = fields.Integer(string="Último número", help='Ingresar el último número del talonario de recibo')
    prefijo = fields.Char(string="Prefijo")
    cantidad_digitos = fields.Integer(string="Cantidad de digitos", default=7)
    numero_actual = fields.Integer(string="Siguiente Número")
    currency_id = fields.Many2one('res.currency', 'Moneda')
    state = fields.Selection([('en_uso', 'En uso'), ('usado', 'Usado')], default='en_uso')
    recibo_ids = fields.One2many('account.recibo', 'talonario_id', string='Recibo', ondelete='set_null')
    es_ultimo_nro = fields.Boolean()
    currency_invoice = fields.Many2one('res.currency', string="Moneda de Factura")
    dif_moneda = fields.Boolean(string="Diferencia de Moneda", default=False)
    cobrar_dif_moneda = fields.Boolean(string="Cobrar Diferencia de Moneda", default=False)
    requiere_caja=fields.Boolean(string='Requiere caja')

    asignar_manualmente = fields.Boolean(string="Asignar nro. manualmente")
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self._get_default_company())


    def agregar_ceros(self, numero, cantidad_digitos):
        numero_str = str(numero)
        cantidad_ceros = cantidad_digitos - len(numero_str)
        ceros = "0" * cantidad_ceros
        return ceros + numero_str

    def _get_default_company(self):
        return self.env.company.id

    @api.onchange('hasta')
    def aparecer_sgte_numero(self):
        for num in self:
            if num.hasta >= num.numero_actual:
                num.es_ultimo_nro = False

    #
    # @api.constrains('usuario_id')
    # def verificar_si_tiene_talonario(self):
    #     for rec in self:
    #         if rec.usuario_id.id:
    #             talonario=self.env['account.recibo.talonario'].search([('usuario_id','=',rec.usuario_id.id),('state','in',['en_uso'])])
    #             if len(talonario)>1:
    #                 raise ValidationError('Este usuario ya tiene un talonario asignado en estado EN USO, debe asignarle a otro usuario')
    #

    def set_utilizado(self):
        for rec in self:
            cantidad_recibo = rec.hasta - rec.desde + 1
            recibos_en_borrador = rec.recibo_ids.filtered(lambda r: r.state == 'borrador')
            if recibos_en_borrador:
                raise ValidationError('Posee recibos en estado "BORRADOR". Favor pase a estado "CONFIRMADO O ANULADO"')
            if (rec.numero_actual - 1) == rec.hasta and cantidad_recibo == len(rec.recibo_ids):
                rec.state = 'usado'
                # talonario_usuario = self.env['res.users'].search([('talonario_recibo_id','=',rec.id)])
                # if talonario_usuario:
                #     talonario_usuario.talonario_recibo_id = None
            else:
                if rec.asignar_manualmente:
                    rec.state = 'usado'
                else:
                    raise ValidationError(
                        'El talonario aún no ha utilizado toda la secuencia de números de recibos asignados para pasar a estado "Utilizado"')

    def set_enuso(self):
        if self.state == 'usado':
            self.state = 'en_uso'

    def unlink(self):
        if self.recibo_ids:
            raise ValidationError("No puede eliminar si su talonario posee recibos")
        return super(models.Model, self).unlink()


class Recibo(models.Model):
    _name = 'account.recibo'
    _order = "id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    # def write(self, vals):
    #     mensaje_error = 'TEST pago es %s' % (self.payment_ids[0].journal_id.name)
    #     raise ValidationError(mensaje_error)
    #     _logger.info('Método write ejecutado con valores: %s', vals)
    #     return super(Recibo, self).write(vals)

    # @api.model
    # def create(self, vals_list):
    #     _logger.info('Método create ejecutado con valores: %s', vals_list)
    #     return super(Recibo, self).create(vals_list)

    def _get_last_number(self):
        for rec in self:
            if rec.talonario_id:
                return rec.talonario_id.numero_actual + 1
                
    @api.onchange('currency_id')
    def check_moneda(self):
        for rec in self:
            if rec.currency_invoice and rec.currency_invoice != rec.currency_id:
                rec.dif_moneda = True
                rec.cobrar_dif_moneda = True
                _logger.warning('check moneda')
            else:
                rec.dif_moneda = False
                rec.cobrar_dif_moneda = False

    def verificar_numeracion_recibo(self):
        for rec in self:
            if rec.talonario_id.numero_actual > rec.talonario_id.hasta:
                raise ValidationError(
                    'El talonario del recibo ya no posee numeros disponibles , Favor contactar con el Jefe de Credito y Cobranza')

            if not rec.name:
                if not rec.talonario_id.asignar_manualmente:
                    if rec.talonario_id.prefijo:
                        rec.name = rec.talonario_id.prefijo + "-" + rec.talonario_id.agregar_ceros(
                            rec.talonario_id.numero_actual, rec.talonario_id.cantidad_digitos)
                    else:
                        rec.name = rec.talonario_id.numero_actual
                    rec.talonario_id.numero_actual = rec._get_last_number()
                    if (rec.talonario_id.numero_actual - 1) == rec.talonario_id.hasta:
                        rec.talonario_id.es_ultimo_nro = True
                else:
                    recibo = self.env['account.recibo'].search(
                        [('name', '=', rec.name), ('talonario_id', '=', rec.talonario_id.id),
                         ('company_id', '=', rec.company_id.id)])
                    if len(recibo) > 1:
                        mensaje = 'El numero de recibo ' + rec.name + ' ya existe para el talonario ' + rec.talonario_id.name + '. Favor verique de vuelta'
                        raise ValidationError(mensaje)
                    if rec.name.isdigit():
                        if int(rec.name) < rec.talonario_id.desde or rec.talonario_id.hasta < int(rec.name):
                            raise ValidationError(
                                'El numero de Recibo no se encuentra en el rango de su Talonario, Favor verifique el numero de recibo o el rango de su talonario')
                        else:
                            if rec.talonario_id.prefijo:
                                numero = int(rec.name)
                                rec.name = rec.talonario_id.prefijo + "-" + rec.talonario_id.agregar_ceros(
                                    numero, rec.talonario_id.cantidad_digitos)

                    # else:
                    #     raise ValidationError('El campo de Nro. de Recibo debe ser numerico')

    def _get_default_user(self):
        return self.env.user.id

    @api.onchange('partner_id')
    def _get_default_talonario(self):
        for rec in self:
            talonario = rec.cobrador.talonario_recibo_ids.filtered(lambda r: r.state == 'en_uso')
            if talonario:
                if len(talonario) == 1:
                    for talos in talonario:
                        rec.talonario_id = talos.id

    name = fields.Char(string="Nro. de Recibo")
    partner_id = fields.Many2one('res.partner', 'Cliente', required=True)
    fecha = fields.Date(string="Fecha", required=True, default=lambda self: fields.Date.context_today(self))
    cobrador = fields.Many2one('res.users', default=lambda self: self._get_default_user())
    talonario_id = fields.Many2one('account.recibo.talonario', 'Talonario',
                                   default=lambda self: self._get_default_talonario(), store=True)
    ultimo_numero = fields.Integer(compute='get_numero_actual', string="Siguiente Numero")
    payment_ids = fields.One2many('account.payment', 'recibo_id', string="Cobros")
    invoice_ids = fields.One2many('account.move', 'recibo_id', string="Facturas", compute='_get_facturas')
    currency_id = fields.Many2one('res.currency', string="Moneda")
    state = fields.Selection([('borrador', 'Borrador'), ('confirmado', 'Confirmado'), ('anulado', 'Anulado')],
                             default='borrador', track_visibility='onchange')
    amount = fields.Float(string="Cantidad a pagar", compute="calcular_monto")
    total_facturas_adeudadas = fields.Float(currency_field="currency_id", string="Total de facturas abiertas",
                                            compute='_calcular_facturas_adeudadas')
    total_cobros = fields.Float(string="Total de cobranzas", compute="_calcular_cobros")

    saldo = fields.Float(string="Saldo", compute="_calcular_saldo")
    motivo_anulacion = fields.Many2one('ruc.motivo.anulacion', string='Motivo de Anulacion')
    pagos_facturas_ids = fields.One2many('account.pago.factura', 'recibo_id')
    dias_en_borrador = fields.Integer()
    move_id = fields.Many2one('account.move', string="Asiento de Diferencia")
    diferencia = fields.Selection(
        [('utilidad', 'Utilidad'), ('a_cuenta', 'A Favor del Cliente/Anticipo'), ('cambio', 'Diferencia de cambio')],
        string="Guardar Diferencia Como:")
    asignar_manualmente = fields.Boolean(related='talonario_id.asignar_manualmente')
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self._get_default_company())
    diferencia_cambio = fields.Float(string="Diferencia de cambio", compute="_verificar_lineas", store=True,
                                     compute_sudo=True)
    diario_diferencia = fields.Many2one('account.journal', 'Diario de diferencia de cambio')
    moneda_company = fields.Boolean(compute="_get_recibo_currency")
    cuenta_diferencia = fields.Many2one('account.account', 'Cuenta Diferencia de cambio')
    move_diferencia_id = fields.Many2one('account.move', 'Asiento de diferencia cambiaria')
    existe_pago_gs_extranjero = fields.Boolean(compute="_verificar_lineas", default=False, store=True,
                                               compute_sudo=True)
    debia_cobrar = fields.Float(compute="_verificar_lineas", store=True, compute_sudo=True)
    cobre = fields.Float(compute="_verificar_lineas", store=True, compute_sudo=True)
    cobrar_dif_moneda = fields.Boolean(string="Activado cobro de diferente moneda")
    currency_invoice = fields.Many2one('res.currency')
    diferencia_2 = fields.Float(compute="_ver2", store=True)
    dif_moneda = fields.Boolean()
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    obs = fields.Text(string="Observaciones", help="Nombre que se utilizará en los apuntes contables")
    tipo = fields.Selection(selection=[
        ('move', 'Por facturas'),
        ('move_line', 'Por apuntes')
    ], string="Tipo", default="move")
    recibo_invoice_ids = fields.Many2many('account.move', compute='_get_invoice_ids', string="Facturas del recibo",
                                          store=True)
    recibo_apunte_ids = fields.Many2many('account.move.line', compute='_get_invoice_ids', string="Facturas del recibo",
                                         store=True)
    get_parcial = fields.Boolean(string="Posee pago parcial", compute='has_partial_payment')
    concepto = fields.Char(string="En concepto de", placeholder="Cancelación de facturas......",
                           help="Este campo se imprimira en la sección en concepto de del recibo")
    concepto_auto = fields.Text(string='En concepto de (automatico)', compute='compute_concepto', store=True)
    print_concepto_auto = fields.Boolean(string="Imprimir concepto automatico en recibo", default=True)

    @api.depends('pagos_facturas_ids.invoice_id')
    def compute_concepto(self):
        for recibo in self:
            conceptos = []
            for linea in recibo.pagos_facturas_ids:
                if linea.invoice_id:
                    conceptos += [str(n) for n in linea.invoice_id.invoice_line_ids.mapped('name') if n]
                else:
                    conceptos.append(str(linea.move_line_id.name))

            recibo.concepto_auto = '\n'.join(conceptos)

    @api.depends('fecha')
    def _compute_fecha_components(self):
        for rec in self:
            if rec.fecha:
                rec.dia = rec.fecha.day
                rec.mes = rec.fecha.month
                rec.ano = rec.fecha.year

    dia = fields.Integer(string="Día", compute='_compute_fecha_components', store=True)
    mes = fields.Integer(string="Mes", compute='_compute_fecha_components', store=True)
    ano = fields.Integer(string="Año", compute='_compute_fecha_components', store=True)

    def monto_cobros_en_lineas(self, moneda):
        """"
           Retorna las lineas dependiendo del la cantidad de caracteres del monto,
           ajustado solo para el recibo comun, con la fuente y tamanio de letra actual
            font-family: Arial, sans-serif; font-size: 18px;

        """
        multi_linea = False
        linea1 = False
        linea2 = False
        if moneda == 'PYG':
            monto_letras = self.calcular_letras(self.total_cobros)
        else:
            monto_letras = self.calcular_letras_dolar(self.total_cobros)

        # para caso de una sola linea
        if len(monto_letras) < 68:
            linea1 = monto_letras
        if len(monto_letras) > 68:
            linea1 = monto_letras[0:68]
            linea2 = monto_letras[68:len(monto_letras)]
            multi_linea = True
        else:
            linea1 = monto_letras

        return multi_linea, linea1, linea2


    @api.depends('pagos_facturas_ids')
    def has_partial_payment(self):
        # mensaje_error = 'TEST pago es hpp %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            get_parcial = None
            for lineas in rec.pagos_facturas_ids:
                if lineas.monto != lineas.residual:
                    get_parcial = True
            rec.get_parcial = get_parcial

    @api.depends('pagos_facturas_ids')
    def _get_invoice_ids(self):
        # mensaje_error = 'TEST pago es gii %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            # list = []
            # for linea in rec.pagos_facturas_ids:
            #     list.append(linea.invoice_id.id)
            rec.recibo_invoice_ids = [(6, 0, rec.pagos_facturas_ids.mapped('invoice_id.id'))]
            rec.recibo_apunte_ids = [(6, 0, rec.pagos_facturas_ids.mapped('move_line_id.id'))]

    @api.onchange('payment_ids')
    def _onchange_payment_ids(self):
        if self.payment_ids:
            # Obtiene el journal_id del primer registro en payment_ids
            print('HOLA')

    @api.onchange('tipo')
    def vaciar_lineas(self):
        # mensaje_error = 'TEST pago es vl %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            rec.pagos_facturas_ids.unlink()
            rec.pagos_facturas_ids = False

    @api.onchange('pagos_facturas_ids')
    def setear_currency_invoice(self):
        # mensaje_error = 'TEST pago es sci %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        """
        El campo currency_invoice del recibo restringe la posibilidad de agregar facturas de diferentes
        monedas en un recibo
        El campo esta oculto y se setea en base a la primera factura cargada
        :return:
        """
        if len(self) == 1:
            if not self.currency_invoice:
                for linea in self.pagos_facturas_ids:
                    self.currency_invoice = linea.currency_invoice
                    break
                if self.currency_invoice and self.currency_invoice != self.env.company.currency_id:
                    rate = self.env['res.currency.rate'].search(
                        [('currency_id', '=', self.currency_invoice.id), ('name', '=', self.fecha)])
                    if not rate:
                        mje = 'La factura se encuentra en otra moneda ' + str(
                            linea.currency_invoice.name) + ' y no existe cotizacion para la fecha del recibo. Favor agregar cotizacion de la fecha ' + str(
                            self.fecha)
                        raise ValidationError(mje)
                    else:
                        if self.currency_id != self.currency_invoice:
                            self.cobrar_dif_moneda = True
                            self.existe_pago_gs_extranjero = True
                        else:
                            self.cobrar_dif_moneda = False
                else:
                    if self.currency_id != self.currency_invoice and self.currency_invoice:
                        self.cobrar_dif_moneda = True
                        self.existe_pago_gs_extranjero = True
                    else:
                        self.cobrar_dif_moneda = False
            else:
                if self.pagos_facturas_ids:
                    for linea in self.pagos_facturas_ids:
                        if linea.invoice_id:
                            if self.currency_invoice != linea.currency_invoice:
                                mje = 'No puede agregar facturas con diferentes monedas en un mismo recibo, la factura número ' + str(
                                    linea.invoice_id.nro_factura) + \
                                      ' tiene como moneda ' + str(
                                    linea.invoice_id.currency_id.name) + ' la factura anterior o anteriores estan con la siguiente moneda ' \
                                      + str(
                                    self.currency_invoice.name) + '. Favor verificar y corregir la carga de facturas'
                                raise ValidationError(mje)
                else:
                    self.currency_invoice = None
                    self.cobrar_dif_moneda = False
                    self.existe_pago_gs_extranjero = False
                    self.dif_moneda = False

    def actualizar_nombre(self):
        # mensaje_error = 'TEST pago es an %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        pagos_rete = self.env['account.payment'].search([('fecha_retencion', '!=', None)])
        i = 0
        for p in pagos_rete:
            m = re.search('[0-9]{3}-[0-9]{3}-[0-9]{7}', p.numero_retencion)
            if not m:
                if p.fecha_retencion <= '2018-12-31':
                    i += 1
                    print('Pago ->', p.id)
                    print('Nro remision ->', p.numero_retencion)
                    print('Fecha pago ->', p.payment_date)
                    print('Fecha retencion ->', p.fecha_retencion)

    @api.depends('payment_ids', 'amount')
    def _ver2(self):
        suma_2 = 0
        if len(self) == 1:
            if self.currency_id != self.env.company.currency_id:
                if self.dif_moneda:
                    for f in self.payment_ids:
                        suma_2 += f.monto_alternativo_2

                        rate_2 = self.env['res.currency.rate'].search(
                            [('currency_id', '=', self.currency_id.id), ('name', '=', self.fecha)])
                        if not rate_2:
                            raise ValidationError('No existe cotizacion para la fecha del recibo')
                        self.diferencia_2 = (self.total_cobros / rate_2.set_venta) - suma_2

    def crear_asiento_dif_cambio(self):
        # mensaje_error = 'TEST pago es cadc %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        vals = self.crear_lineas_de_asientos()
        move_vals = vals.get('move_vals', {})
        debit_line_vals = vals.get('debit_line_vals', {})
        credit_line_vals = vals.get('credit_line_vals', {})
        move = self.env['account.move'].create(move_vals)
        for deb in debit_line_vals:
            deb['move_id'] = move.id
            move.line_ids.with_context(check_move_validity=False).create(deb)
        for cred in credit_line_vals:
            cred['move_id'] = move.id
            move.line_ids.with_context(check_move_validity=False).create(cred)
        move._post()
        self.move_diferencia_id = move

    def crear_lineas_de_asientos(self):
        # mensaje_error = 'TEST pago es cla %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        vals_cred = list()
        vals_debit = list()
        ref = 'Diferencia de tasa de cambio Recibos ' + self.name
        journal = self.env['account.journal'].search([('name', '=', 'Diferencia de cambio'), (
            'company_id', '=', self.env.company.id)], limit=1)
        seq_id = self.env['ir.sequence'].search([('id', '=', journal.sequence_id.id)])
        name = seq_id._next()
        date = self.fecha
        move_vals = {
            'name': name,
            'journal_id': journal.id,
            'date': date,
            'ref': ref,
        }
        # _logger.warning('moveeee %s', move_vals)
        rate = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency_id.id), ('name', '=', self.fecha)])
        pay = self.payment_ids.filtered(lambda r: r.journal_id.type in ('bank', 'cash'))

        for payments in pay:
            if payments.monto_alternativo_2 > 0:
                acor = round(rate.set_venta * payments.monto_alternativo_2 - (payments.amount))
                if acor > 0:
                    vls = {
                        'name': ref,
                        'account_id': payments.journal_id.default_account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': abs(acor),
                        'reconciled': True,
                        'credit': 0,
                        'ref': ref,
                    }
                    vals_debit.append(vls)
                else:
                    vls = {
                        'name': ref,
                        'account_id': payments.journal_id.default_account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': 0,
                        'credit': abs(acor),
                        'ref': ref,
                    }
                    vals_cred.append(vls)

        acor = abs(self.diferencia_2 * rate.set_venta)
        if self.diferencia_2 > 0:
            debit_line_vals = {
                'name': ref,
                'account_id': journal.default_account_id.id,
                'partner_id': self.partner_id.id,
                'debit': round(acor),
                'credit': 0,
                'ref': ref,
            }
            vals_debit.append(debit_line_vals)
        else:
            credit_line_vals = {
                'name': ref,
                'account_id': journal.default_account_id.id,
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'debit': 0,
                'credit': round(acor),
                'ref': ref,
            }
            vals_cred.append(credit_line_vals)
        self.verificar_descuadre(vals_debit, vals_cred)
        return {
            'move_vals': move_vals,
            'debit_line_vals': vals_debit,
            'credit_line_vals': vals_cred,
        }

    @api.depends('payment_ids', 'amount', 'pagos_facturas_ids', 'total_cobros')
    def _verificar_lineas(self):
        # mensaje_error = 'TEST pago es vl %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            suma = 0
            rec.diferencia_cambio = 0
            rec.existe_pago_gs_extranjero = False
            if rec.currency_invoice and rec.currency_invoice != self.env.company.currency_id:
                rate = self.env['res.currency.rate'].search(
                    [('currency_id', '=', rec.currency_invoice.id), ('name', '=', rec.fecha)])
                if not rate:
                    raise ValidationError('No existe cotizacion para la fecha del recibo')
                else:
                    rate = rate[0]
                    rec.existe_pago_gs_extranjero = True
                    total_mon = rec.total_cobros * rate.set_venta
                for f in rec.payment_ids:
                    if f.monto_moneda_pago > 0:
                        suma += f.monto_moneda_pago
                if rec.cobrar_dif_moneda:
                    rec.debia_cobrar = total_mon
                    rec.cobre = suma
                    suma = suma - total_mon
                rec.diferencia_cambio = suma
                journal = self.env['account.journal'].search([('exchange_rate_journal', '=', True), (
                    'company_id', '=', self.env.company.id)], limit=1)

                cuenta_ganancia = self.env['res.config.settings'].sudo().search([], limit=1,
                                                                                order="id desc").income_currency_exchange_account_id
                cuenta_perdida = self.env['res.config.settings'].sudo().search([], limit=1,
                                                                               order="id desc").expense_currency_exchange_account_id
                if rec.diferencia_cambio > 0:
                    rec.cuenta_diferencia = cuenta_ganancia
                elif rec.diferencia_cambio < 0:
                    rec.cuenta_diferencia = cuenta_perdida
            elif rec.currency_invoice != rec.currency_id:
                if rec.cobrar_dif_moneda:
                    rate = self.env['res.currency.rate'].search(
                        [('currency_id', '=', rec.currency_invoice.id), ('name', '=', rec.fecha)])
                    if not rate:
                        raise ValidationError('No existe cotizacion para la fecha del recibo')
                    rate = rate[0]
                    rec.existe_pago_gs_extranjero = True
                    total_mon = sum(p.monto_moneda_pago for p in rec.payment_ids)
                    rec.debia_cobrar = rec.total_cobros
                    rec.cobre = total_mon
                    rec.diferencia_cambio = rec.cobre - rec.debia_cobrar
            else:
                rec.existe_pago_gs_extranjero = False
                rec.diferencia_cambio = 0

    @api.depends('currency_id')
    def _get_recibo_currency(self):
        # mensaje_error = 'TEST pago es grc %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            if rec.currency_id != self.env.company.currency_id:
                rec.moneda_company = False
            else:
                rec.moneda_company = True

    def set_pagofactura(self):
        # mensaje_error = 'TEST pago es spf %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        pagofactura = self.env['account.pago.factura'].search([])
        for f in pagofactura:
            if f.invoice_id.move_type in ('out_invoice', 'in_invoice'):
                f.amount_total = f.invoice_id.amount_total
                f.residual = f.invoice_id.amount_residual
            else:
                f.amount_total = f.invoice_id.amount_total_signed
                f.residual = f.invoice_id.amount_residual_signed

    @api.depends('pagos_facturas_ids.invoice_id')
    def _get_facturas(self):
        # mensaje_error = 'TEST pago es gf %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        facs = list()
        for rec in self:
            if rec.pagos_facturas_ids:
                for p in rec.pagos_facturas_ids:
                    if p.invoice_id:
                        facs.append(p.invoice_id.id)
        rec.invoice_ids = [(6, 0, facs)]
        return True

    @api.onchange('fecha')
    def agregar_al_context(self):
        # mensaje_error = 'TEST pago es aac %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        if self.fecha:
            self = self.with_context(fecha=self.fecha)

    def _get_default_company(self):
        return self.env.company.id

    def funcion_cargar_lineas_facturas(self):
        if self.partner_id:
            facturas = self.env['account.move'].search(
                [('partner_id', 'child_of', self.partner_id.id), ('currency_id', '=', self.currency_id.id),
                 ('state', '=', 'open')])
            for f in facturas:
                if f.type in ('out_refund', 'in_refund'):
                    monto = f.residual_signed
                    amount = f.residual_signed
                    amount_total = f.amount_total
                    residual = f.residual_signed
                else:

                    monto = f.residual
                    amount = f.residual
                    amount_total = f.amount_total
                    residual = f.residual
                pago_fact = self.env['account.pago.factura']

                datos = {
                    'invoice_id': f.id,
                    'partner_id': self.partner_id.id,
                    'currency_id': self.currency_id.id,
                    'invoice_date': f.invoice_date,
                    'nro_factura': f.nro_factura,
                    'recibo_id': self.id,
                    'monto': monto,
                    'amount': amount,
                    'amount_total': amount_total,
                    'residual': residual
                }
                pago_fact.create(datos)
                f.no_ver_factura = True
        else:
            raise ValidationError('Debe asignar primero un cliente')

    def eliminar_todas_lineas_facturas(self):
        for f in self.pagos_facturas_ids:
            f.unlink()

    @api.depends('total_cobros', 'amount')
    def _calcular_saldo(self):
        # mensaje_error = 'TEST pago es cs %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            print("_calcular_saldo")
            # rec.saldo = round((rec.amount - rec.total_cobros), 2)
            if rec.currency_invoice:
                if 'USD' in rec.currency_invoice.name:
                    print(f"amount->{rec.amount}")
                    print(f"total_cobros->{rec.total_cobros}")
                    _logger.info('amount %s' % rec.amount)
                    _logger.info('total_cobros %s' % rec.total_cobros)
                    saldo = round((rec.amount - rec.total_cobros), 2)
                    if round(saldo) != 0:
                        rec.saldo = saldo
                    else:
                        rec.saldo = round(saldo)
                else:
                    rec.saldo = (rec.amount - rec.total_cobros)
            else:
                rec.saldo = round((rec.amount - rec.total_cobros), 2)

    def redondeo_por_tres_cifras(self, numero, ajuste, moneda):

        print(type(numero))
        if type(numero) is float:
            nuevo_numero = str(numero).split('.')
            decimal1 = 0
            decimal2 = 0
            decimal3 = 0
            if nuevo_numero[1][:1]:
                decimal1 = int(nuevo_numero[1][:1])
            if nuevo_numero[1][1:2]:
                decimal2 = int(nuevo_numero[1][1:2])
            if nuevo_numero[1][2:3]:
                decimal3 = int(nuevo_numero[1][2:3])
            numero = int(numero)
            if 'PYG' in moneda:
                if decimal3 >= ajuste and (decimal2 + 1) >= ajuste and (decimal1 + 1) >= ajuste:
                    numero += 1
                    flotante = float(numero)
                    return flotante
                elif decimal3 >= ajuste and (decimal2 + 1) >= ajuste and (decimal1 + 1) < ajuste:
                    decimal1 += 1
                    letter_decimal = str(decimal1) + '0'
                    flotante = float(str(numero) + '.' + letter_decimal)
                    return flotante
                elif decimal3 >= ajuste and (decimal2 + 1) <= ajuste:
                    decimal2 += 1
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    return flotante
                elif decimal3 < ajuste and decimal2 < ajuste and decimal1 < ajuste:
                    if decimal2 != 0 or decimal1 != 0:
                        letter_decimal = str(decimal1) + str(decimal2)
                        flotante = float(str(numero) + '.' + letter_decimal)
                        return flotante
                    elif decimal2 == 0 and decimal1 == 0:
                        flotante = float(numero)
                        return flotante
                elif decimal3 < ajuste and decimal2 >= ajuste and (decimal1 + 1) < ajuste:
                    decimal1 += 1
                    letter_decimal = str(decimal1) + '0'
                    flotante = float(str(numero) + '.' + letter_decimal)
                    return flotante
                elif decimal3 < ajuste and decimal2 < ajuste and decimal1 >= ajuste:
                    numero += 1
                    flotante = float(numero)
                    return flotante
            else:
                print(numero)
                if decimal3 >= ajuste and (decimal2 + 1):
                    decimal2 += 1
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
                elif decimal3 < ajuste and decimal2 < ajuste and decimal1 < ajuste:
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
                elif decimal3 < ajuste and decimal2 >= ajuste and decimal1 < ajuste:
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
                elif decimal3 < ajuste and decimal2 >= ajuste and decimal1 >= ajuste:
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
                elif decimal3 < ajuste and decimal2 < ajuste and decimal1 >= ajuste:
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
                elif decimal3 > ajuste and (decimal2 + 1) < ajuste and decimal1 < ajuste:
                    decimal2 += 1
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
                elif decimal3 >= ajuste and (decimal2 + 1) < ajuste and decimal1 >= ajuste:
                    decimal2 += 1
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
                elif decimal3 >= ajuste and (decimal2 + 1) < ajuste and decimal1 < ajuste:
                    decimal2 += 1
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
        else:
            return numero

    @api.depends('payment_ids')
    def _calcular_cobros(self):
        # mensaje_error = 'TEST pago es cc %s' % (self.payment_ids[0].journal_id)
        # raise ValidationError(mensaje_error)
        # _logger.warning(mensaje_error)
        cuentas = self.get_invoices_move_accounts()
        for rec in self:
            if rec.payment_ids:
                for p in rec.payment_ids:
                    _logger.warning('p diario es %s', p.journal_id)
                    if cuentas:
                        lineas = p.line_ids
                        contralinea = lineas.filtered(lambda r: r.account_id.account_type == 'asset_receivable')
                        # if contralinea:
                        #     contralinea[0].account_id = cuentas.id
                    rec.total_cobros += p.amount
            else:
                rec.total_cobros = 0

    def get_invoices_move_accounts(self):
        # mensaje_error = 'TEST pago es gim %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            cuentas_dict = {}
            tot_cuen = 0
            cuentas = rec.pagos_facturas_ids.mapped('account_receivable')
            if len(cuentas) > 0:
                return cuentas[0]
            else:
                return cuentas

    @api.depends('invoice_ids')
    def _calcular_facturas_adeudadas(self):
        for rec in self:
            if rec.invoice_ids:
                total = 0
                for f in rec.invoice_ids:
                    total += f.residual
                rec.total_facturas_adeudadas = total
            else:
                rec.total_facturas_adeudadas = 0

    @api.constrains('payment_ids')
    def verificar_pago(self):
        # mensaje_error = 'TEST pago es vp %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            if rec.payment_ids:
                pagos_distintos = rec.payment_ids.filtered(lambda
                                                               record: record.partner_id != rec.partner_id and record.partner_id.parent_id != rec.partner_id)
                if pagos_distintos:
                    raise ValidationError(
                        'No pueden crearse recibos con pagos relacionados a empresas distintas a la detallada en el recibo')

    @api.depends('pagos_facturas_ids')
    def calcular_monto(self):
        # mensaje_error = 'TEST pago es cm %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        for rec in self:
            rec.amount = 0
            for f in rec.pagos_facturas_ids:
                rec.amount += f.monto

    def confirmar_recibo(self):

        self.verificar_numeracion_recibo()
        if self.currency_id != self.env.company.currency_id:
            coti = self.env['res.currency.rate'].search(
                [['name', '=', self.fecha],
                 ['currency_id', '=', self.currency_id.id]])
            if not coti:
                raise ValidationError(
                    'No se encuentra cotizacion %s para la fecha del Recibo %s . Verifique que la cotizacion se encuentre cargada ' % (
                        self.currency_id.name, str(
                            self.fecha)))
        if self.saldo > 1:
            raise ValidationError(
                'Hay una diferencia entre el Monto de la Factura y el Cobro, Favor fijarte en el campo "DIFERENCIA" debe ser igual a 0')

        if self.saldo < 0:

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'diferencia.recibo',
                'context': {'default_recibo': self.id},
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            self.set_confirmado()

    def set_confirmado(self):
        domain_pago = ([('account_type', '=', 'asset_receivable')])
        cheques = list()
        to_reconcile = self.env['account.move.line']
        if self.state != 'confirmado':
            #             self.set_amount_gs()
            if self.talonario_id:
                if self.payment_ids:
                    # DONDE SE APLICA LA RETENCION A LAS FACTURAS CON MAYOR MONTOS PRIMERAMENTE
                    nc = self.pagos_facturas_ids.filtered(
                        lambda r: r.invoice_id.amount_residual > 0 and r.invoice_id.move_type in (
                        'out_refund', 'in_refund'))
                    if nc:
                        for nota in nc:
                            # SI EN EL CASO LA NOTA DE CREDITO QUEDA CON SALDO QUE APLIQUE A LAS SIGUIENTE FACTURA
                            while (nota.invoice_id.amount_residual > 0):
                                for fac in self.pagos_facturas_ids.filtered(
                                        lambda r: r.amount > 0 and r.invoice_id.move_type == 'out_invoice').sorted(
                                    key=lambda r: r.amount, reverse=True):
                                    # if fac.amount == fac.invoice_id.amount_residual:
                                    # BUSCAMOS EL REGISTRO DE LA NOTA DE CREDITO YA QUE SOLO TENEMOS EL ID QUE ESTA DENTRO DE NOTAS
                                    nota_de_credito = self.env['account.move'].search(
                                        [['id', '=', nota.invoice_id.id]])
                                    # VERIFICAMOS IS LA NOTA DE CREDITO TIENE SALDO MAYOR A 0
                                    if nota_de_credito.residual > 0:
                                        # SI LA NOTA DE CREDITO TIENE SALDO MAYOR A 0 BUSCAMOS LA LINEA DE ASIENTO QUE CORRESPONDE A ESA NOTA DE CREDITO
                                        nota_credito_line = self.env['account.move.line'].search(
                                            [['invoice_id', '=', nota.invoice_id.id], ['user_type_id', '=', 1]])

                                        # ASIGNAMOS EL VALOR DEL SALDO DE LA NOTA DE CREDITO A LA FACTURA QUE SE ESTA ITERANDO EN ESTE MOMENTO
                                        if fac.invoice_id.amount_residual > nota.invoice_id.amount_residual:
                                            fac.amount -= nota_de_credito.residual
                                        else:
                                            fac.amount -= fac.invoice_id.amount_residual
                                        fac.invoice_id.assign_outstanding_credit(nota_credito_line.id)
                                    if nota_de_credito.residual == 0:
                                        break

                    for p in self.payment_ids.sorted(key=lambda r: r.amount, reverse=True):
                        diario = p.journal_id
                        if p.cheque_tercero:
                            if p.currency_id != p.moneda_pago:
                                moneda = p.moneda_pago.id
                            else:
                                moneda = p.currency_id.id
                            cheque_tercero = self.env['account.check.third'].search(
                                [('number', '=', p.numero_cheque_recibo),
                                 ('bank_id', '=', p.banco_cheque_recibo.id)])
                            if p.monto_cheque_recibo != 0:
                                monto_cheque_recibo = p.monto_cheque_recibo
                            else:
                                monto_cheque_recibo = p.amount
                            if not cheque_tercero:
                                cheque_tercero = self.env['account.check.third']

                                datos = {
                                    'number': p.numero_cheque_recibo,
                                    'amount': monto_cheque_recibo,
                                    # 'issue_date': datetime.strftime(date.today(),"%d/%m/%Y"),
                                    'bank_id': p.banco_cheque_recibo.id,
                                    'cuit': p.nro_cuenta_recibo,
                                    'payment_date': p.fecha_cheque_diferido,
                                    'issue_date': p.fecha_cheque_recibo,
                                    'tipo_cheque': p.tipo_de_cheque_recibo,
                                    'voucher_id': p.id,
                                    'journal_id': p.journal_id.id,
                                    'recibo': p.recibo_id.name,
                                    'source_partner_id': p.partner_id.id,
                                    'owner_name': p.titular_recibo,
                                    'currency_id': moneda,
                                }
                                cheque_tercero.create(datos)
                            else:
                                # raise ValidationError('No se puede duplicar numero de Cheque. Cheque nro %s ya existe en el sistema' % p.numero_cheque)
                                datos = {
                                    'owner_name': p.titular_recibo,
                                    'journal_id': p.journal_id.id,
                                    'bank_id': p.banco_cheque_recibo.id,
                                    'cuit': p.nro_cuenta_recibo,
                                    'payment_date': p.fecha_cheque_diferido,
                                    'issue_date': p.fecha_cheque_recibo,
                                    'amount': monto_cheque_recibo + cheque_tercero.amount,
                                    'tipo_cheque': p.tipo_de_cheque_recibo,
                                    'number': p.numero_cheque_recibo,
                                    'currency_id': moneda,
                                }
                                cheque_tercero.write(datos)

                        pago = p.amount

                        facturas = self.pagos_facturas_ids.filtered(
                            lambda r: r.invoice_id.amount_residual > 0 and r.invoice_id.move_type not in (
                                'out_refund', 'in_refund'))

                        for i in facturas.sorted(key=lambda r: r.monto, reverse=True):
                            if pago > 0:
                                if not i.invoice_id.move_type in ('out_refund', 'in_refund'):
                                    if i.amount == 0:
                                        i.verificar_amount()
                                    if pago <= i.amount:
                                        i.amount -= pago
                                        i.invoice_id.monto_a_pagar = pago
                                        p.reconciled_invoice_ids = [(4, i.invoice_id.id)]
                                        pago = 0
                                    else:
                                        pago -= i.amount
                                        i.invoice_id.monto_a_pagar = i.amount
                                        p.reconciled_invoice_ids = [(4, i.invoice_id.id)]
                                        i.amount = 0
                                    to_reconcile += (i.invoice_id.line_ids.filtered_domain(domain_pago))
                            else:
                                break
                        apuntes = self.pagos_facturas_ids.filtered(
                            lambda r: r.move_line_id.amount_residual != 0)

                        for i in apuntes.sorted(key=lambda r: r.monto, reverse=True):
                            if i.amount == 0:
                                i.verificar_amount()
                            if pago <= i.amount:
                                i.amount -= pago
                                i.move_line_id.monto_a_pagar = pago
                                p.reconciled_invoice_ids = [(4, i.move_line_id.move_id.id)]
                                pago = 0
                            else:
                                pago -= i.amount
                                i.move_line_id.monto_a_pagar = i.amount
                                p.reconciled_invoice_ids = [(4, i.move_line_id.move_id.id)]
                                i.amount = 0

                            to_reconcile += (i.move_line_id)

                        cuentas = self.get_invoices_move_accounts()
                        print('aaaaa')
                        print(cuentas)
                        if not cuentas:
                            cuentas = self._context.get('cuenta_utilidad')

                        p.with_context(cuenta=cuentas)._compute_destination_account_id()
                        p.action_post()
                        payment_lines = p.line_ids.filtered_domain(domain_pago)
                        p.recibo_id = self.id
                        print('recibiooo')
                        for account in payment_lines.account_id:
                            (payment_lines + to_reconcile) \
                                .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                                .with_context(recibo=self, has_partial=self.get_parcial).reconcile()
                    if pago > 0:
                        if self.saldo != 0:
                            if self.saldo < 0:
                                self.asiento_utilidad(pago, diario, self.currency_id)
                            else:
                                ValidationError('Error al confirmar el recibo')
                    if self.diferencia_cambio != 0:
                        self._crear_diferencia_cambio()
                    self.state = 'confirmado'
                    self.dias_en_borrador = 0
                    # Los residuales se actualiza para la vista quede bien
                    for i in self.pagos_facturas_ids:
                        if i.invoice_id.move_type in ('out_invoice', 'in_invoice'):
                            i.residual = i.invoice_id.amount_residual
                        else:
                            i.residual = i.invoice_id.amount_residual_signed
                else:
                    raise ValidationError('No tiene asociado ninguna "Factura o Cobro" al Recibo')
            else:
                raise ValidationError('Favor seleccionar un talonario de recibo')
        self.post_caja_recibo()

    def _crear_diferencia_cambio(self):
        for recibo in self:
            if recibo.diferencia_cambio != 0:
                diario_diferencia = self.env.company.currency_exchange_journal_id
                if recibo.currency_invoice != self.env.company.currency_id:
                    self.asiento_diferencia(recibo.diferencia_cambio, diario_diferencia, recibo.currency_invoice)
                else:
                    self.asiento_diferencia(recibo.diferencia_cambio, diario_diferencia, recibo.currency_id)

    def asiento_diferencia(self, pago, diario, moneda):
        rate_recibo = \
        self.env['res.currency.rate'].search([('currency_id', '=', moneda.id), ('name', '=', self.fecha)])[0].set_venta
        fecha = self.fecha
        vals = self.get_vals_cambio(pago, fecha, diario, moneda)
        move_vals = vals.get('move_vals', {})
        debit_line_vals = vals.get('debit_line_vals', {})
        credit_line_vals = vals.get('credit_line_vals', {})
        move = self.env['account.move'].with_context(check_move_validity=False).create(move_vals)
        for deb in debit_line_vals:
            deb['move_id'] = move.id
            move.line_ids.with_context(check_move_validity=False).create(deb)
        for cred in credit_line_vals:
            cred['move_id'] = move.id
            move.line_ids.with_context(check_move_validity=False).create(cred)
        lines_to_reconcile = list()
        move._post()
        self.move_diferencia_id = move

    @api.model
    def get_vals_cambio(self, suma, date, diario, moneda):
        vals_cred = list()
        vals_debit = list()
        val_c = 0
        val_d = 0
        ref = 'Diferencia de tasa de cambio Recibo Nr ' + self.name
        journal = diario
        cuenta_ganancia = self.env.company.income_currency_exchange_account_id
        cuenta_perdida = self.env.company.expense_currency_exchange_account_id

        if not cuenta_ganancia or not cuenta_perdida:
            raise ValidationError(
                'Favor especificar cuenta de ganancia y pérdida por tasa cambiaria en ajustes de la compañía')
        # journal = diario
        if suma < 0:
            credit_account_id = self.cuenta_diferencia.id
            debit_account_id = self.cuenta_diferencia.id
            val_d = 1
        else:
            credit_account_id = self.cuenta_diferencia.id
            debit_account_id = self.cuenta_diferencia.id
            val_c = 1
        name = ref

        move_vals = {
            # 'name': name,
            'journal_id': journal.id,
            'date': date,
            'ref': ref,
        }

        rate = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency_invoice.id), ('name', '=', self.fecha)])

        pay = self.payment_ids.filtered(lambda r: r.journal_id.type in ('bank', 'cash'))

        for payments in pay:
            if payments.monto_moneda_pago > 0:
                rate2 = self.env['res.currency.rate'].search(
                    [('currency_id', '=', self.currency_invoice.id), ('name', '=', payments.date)])
                redondeo = self.currency_invoice.rounding
                acor_2 = payments.monto_moneda_pago - (rate2.set_venta * payments.amount)
                acor = float_round(acor_2, precision_rounding=redondeo, rounding_method='HALF-UP')
                print(acor)
                if acor > 0:
                    vls = {
                        'name': ref,
                        'account_id': payments.journal_id.default_account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': abs(acor),
                        'reconciled': True,
                        'credit': 0,
                        'ref': ref,
                    }
                    vals_debit.append(vls)
                else:
                    vls = {
                        'name': ref,
                        'account_id': payments.journal_id.default_account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': 0,
                        'credit': abs(acor),
                        'ref': ref,
                    }
                    vals_cred.append(vls)

        acor = abs(self.diferencia_cambio)
        if self.currency_invoice == self.currency_id and self.currency_invoice != self.env.company.currency_id and self.cantidad_retenciones > 0:
            if suma < 0:
                suma = 1
            else:
                suma = -1
        if suma < 0:
            debit_line_vals = {
                'name': ref,
                'account_id': cuenta_ganancia.id,
                'partner_id': self.partner_id.id,
                'debit': float_round(acor, precision_rounding=0.001, rounding_method='HALF-UP'),
                'credit': 0,
                'ref': ref,
            }
            vals_debit.append(debit_line_vals)
        else:
            credit_line_vals = {
                'name': ref,
                'account_id': cuenta_ganancia.id,
                'partner_id': self.partner_id.id,
                'debit': 0,
                'credit': float_round(acor, precision_rounding=0.001, rounding_method='HALF-UP'),
                'ref': ref,
            }
            vals_cred.append(credit_line_vals)
        self.verificar_descuadre(vals_debit, vals_cred)
        return {
            'move_vals': move_vals,
            'debit_line_vals': vals_debit,
            'credit_line_vals': vals_cred,
        }

    def verificar_descuadre(self, vals_debit, vals_cred):
        # mensaje_error = 'TEST pago es vd %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        """
        Funcion que verifica que si hay descuadre de hasta 2 hace cuadrar, porque lo mas probable que el descuadre
        se deba por redondeo
        :param vals_debit:
        :param vals_cred:
        :return:
        """
        suma_debito = sum([d['debit'] for d in vals_debit])
        suma_credito = sum([c['credit'] for c in vals_cred])

        if suma_credito != suma_debito and suma_credito > 0 and suma_debito > 0:
            dif = suma_debito - suma_credito
            ban = 0
            if dif <= 2 and dif > 0:
                for d in vals_debit:
                    if d['debit'] > dif:
                        d['debit'] -= dif
                        ban = 1
                        break
                if ban == 0:
                    for c in vals_cred:
                        if c['credit'] > dif:
                            c['credit'] -= dif
                            ban = 1
                            break

            if dif >= -2 and dif < 0:
                dif = abs(dif)
                for c in vals_cred:
                    if c['credit'] > dif:
                        c['credit'] -= dif
                        ban = 1
                        break
                if ban == 0:
                    for d in vals_debit:
                        if d['debit'] > dif:
                            d['debit'] -= dif
                            ban = 1
                            break

    def asiento_utilidad(self, pago, diario, moneda):
        # mensaje_error = 'TEST pago es au %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        if pago > 0:
            fecha = self.fecha
            pago_moneda = 0
            if moneda != self.env.company.currency_id:
                rate = self.env['res.currency.rate'].search([['name', '=', fecha], ['currency_id', '=', moneda.id]])
                pago_moneda = pago
                pago = pago * rate.set_venta
            elif self.currency_id != self.currency_invoice and self.currency_invoice != self.env.company.currency_id:
                rate = self.env['res.currency.rate'].search(
                    [['name', '=', fecha], ['currency_id', '=', self.currency_invoice.id]])
                pago_moneda = pago
                pago = pago * rate.set_venta
                moneda = self.currency_invoice
            vals = self.get_vals(pago, fecha, diario, pago_moneda, moneda)

            # extraemos los vals
            move_vals = vals.get('move_vals', {})
            debit_line_vals = vals.get('debit_line_vals', {})
            credit_line_vals = vals.get('credit_line_vals', {})
            # check_move_field = vals.get('check_move_field')
            signal = vals.get('signal')

            move = self.env['account.move'].with_context({}).create(move_vals)
            debit_line_vals['move_id'] = move.id
            credit_line_vals['move_id'] = move.id

            move.line_ids.with_context(check_move_validity=False).create(debit_line_vals)
            move.line_ids.with_context(check_move_validity=False).create(credit_line_vals)

            # check.write({check_move_field: move.id})
            # check.action_deposit();
            move._post()
            self.move_id = move

    def get_vals(self, suma, date, diario, pago_moneda, moneda):
        # mensaje_error = 'TEST pago es gv %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        # vou_journal = check.voucher_id.journal_id

        # if self.action_type == 'deposit':
        if moneda == self.env.company.currency_id:
            moneda = None
            pago_moneda = 0
        else:
            moneda = moneda.id

        ref = 'Pago de Recibo Nro. ' + self.name
        # check_move_field = 'deposit_account_move_id'
        journal = self.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', self.env.company.id)], limit=1)
        debit_account_id = diario.default_account_id.id
        if self.diferencia == 'utilidad':
            credit_account_id = self.env.company.cuenta_utilidad_recibo.id
        else:
            credit_account_id = self.partner_id.property_account_receivable_id.id
            diario_banco = self.payment_ids.filtered(lambda x: x.journal_id.type == 'bank')
            if len(diario_banco) > 0:
                debit_account_id = diario_banco[0].journal_id.default_account_id.id

        signal = 'Excedente Recibo Nro.' + self.name
        monto_mon_ex_c = None
        monto_mon_ex_d = None

        # ref += check.name
        move_vals = {
            'journal_id': journal.id,
            'date': date,
            'ref': ref,
        }

        debit_line_vals = {
            'name': ref,
            'account_id': debit_account_id,
            'partner_id': self.partner_id.id,
            'debit': suma,
            'currency_id': moneda,
            'amount_currency': pago_moneda,
            'credit': 0,
            'ref': ref,

        }

        # raise exceptions.ValidationError(debit_line_vals['ref'])
        credit_line_vals = {
            'name': ref,
            'account_id': credit_account_id,
            'partner_id': self.partner_id.id,
            'currency_id': moneda,
            'amount_currency': -1 * pago_moneda,
            'debit': 0,
            'credit': suma,
            'ref': ref,
        }
        # raise exceptions.ValidationError(credit_line_vals['amount_currency'])
        return {
            'move_vals': move_vals,
            'debit_line_vals': debit_line_vals,
            'credit_line_vals': credit_line_vals,

            'signal': signal,
        }

    def set_borrador(self):
        if self.state == 'confirmado':
            for p in self.payment_ids:
                p.with_context(skip_account_move_synchronization=True).action_draft()
                p.reconciled_invoice_ids = [(5, 0, 0)]
                p.state = 'draft'
                # for f in p.fac_ids:
                # p.fac_ids.unlink()

            if self.payment_ids:
                for pay in self.payment_ids:
                    moves = self.env['account.move.line'].search([('payment_id', '=', pay.id)])
                    if len(moves) > 0:
                        for m in moves:
                            if m.full_reconcile_id:
                                m.full_reconcile_id.partial_reconcile_ids.unlink()
                            m.remove_move_reconcile()

            if self.move_id:
                for move in self.move_id:

                    for lineas in move.line_ids:
                        lineas.remove_move_reconcile()
                    move.button_cancel()
                    move.unlink()
            if self.move_diferencia_id:
                for move in self.move_diferencia_id:
                    for lineas in move.line_ids:
                        lineas.remove_move_reconcile()
                    move.button_cancel()
                    move.unlink()
            for fac in self.pagos_facturas_ids.filtered(
                    lambda r: r.invoice_id.move_type in ('out_refund', 'in_refund')):
                movelines = fac.invoice_id.move_id.line_ids
                for line in movelines:
                    if line.reconciled:
                        line.remove_move_reconcile()
                fac.amount = 0
            for fac in self.pagos_facturas_ids:
                if fac.invoice_id.move_type in ('out_invoice', 'in_invoice'):
                    fac.residual = fac.invoice_id.amount_residual
                else:
                    fac.residual = fac.invoice_id.amount_residual_signed


        else:
            self.motivo_anulacion = None
        # self.state = 'borrador'

        detalle_caja = self.env['ruc.caja.detalle'].search([('recibo_id.id', '=', self.id)])

        if len(detalle_caja) > 1:
            for i in detalle_caja:
                if i.caja_id.state == 'abierto':
                    if len(i.cobro_cheque) > 0:
                        for cheques in i.cobro_cheque:
                            cheques.action_cancel()
                            cheques.unlink()
                    i.unlink()
                # else:
                #      raise ValidationError('La caja ya NO se encuentra Abierta, NO puede pasar a borrador el recibo')
        else:
            if detalle_caja.caja_id.state == 'abierto':
                if len(detalle_caja.cobro_cheque) > 0:
                    for cheques in detalle_caja.cobro_cheque:
                        cheques.action_cancel()
                        cheques.unlink()
                detalle_caja.unlink()
            # else:
            #     raise ValidationError('La caja ya NO se encuentra Abierta, NO puede pasar a borrador el recibo')
        self.state = 'borrador'

    @api.onchange('partner_id')
    def limpiar_lineas_facturas(self):
        # mensaje_error = 'TEST pago es llf %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        if self.pagos_facturas_ids:
            raise ValidationError('Elimine las facturas que se agrego del cliente anterior')
        if self.payment_ids:
            raise ValidationError('Elimine los cobros que se agrego del cliente anterior')

    @api.onchange('pagos_facturas_ids', 'partner_id')
    def ver_facturas(self):
        # mensaje_error = 'TEST pago es vf %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        if self.partner_id:
            lista_factura = []
            lista_facturas_abiertas = []
            lista_a_mostrar = []

            fac_abiertas = self.env['account.move'].search(
                [('partner_id', 'child_of', self.partner_id.id), ('state', '=', 'open'),
                 ('move_type', '=', 'out_invoice')])

            for rec in self.pagos_facturas_ids:
                if rec.invoice_id:
                    lista_factura.append(rec.invoice_id)
            for f in fac_abiertas:
                if f.no_ver_factura_recibo:
                    dato = {
                        'no_ver_factura_recibo': False
                    }
                    f.write(dato)
                lista_facturas_abiertas.append(f)

            lista_factura = set(lista_factura)
            lista_facturas_abiertas = set(lista_facturas_abiertas)
            lista_a_mostrar = lista_factura & lista_facturas_abiertas
            for f in lista_a_mostrar:
                dato = {
                    'no_ver_factura_recibo': True
                }
                f.write(dato)

    def limpiar_facturas(self):
        # mensaje_error = 'TEST pago es lf %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        if self.partner_id:
            lista_factura = []
            lista_facturas_abiertas = []

            lista_a_mostrar = []
            fac_abiertas = self.env['account.move'].search(
                [('partner_id', '=', self.partner_id.id), ('state', '=', 'open')])
            for rec in self.pagos_facturas_ids:
                if rec.invoice_id:
                    lista_factura.append(rec.invoice_id)
            for f in fac_abiertas:
                if f.no_ver_factura_recibo:
                    dato = {
                        'no_ver_factura_recibo': False
                    }
                    f.write(dato)
                lista_facturas_abiertas.append(f)

            lista_factura = set(lista_factura)
            lista_facturas_abiertas = set(lista_facturas_abiertas)
            lista_a_mostrar = lista_factura & lista_facturas_abiertas
            for f in lista_a_mostrar:
                dato = {
                    'no_ver_factura_recibo': True
                }
                f.write(dato)

    @api.depends('talonario_id')
    def get_numero_actual(self):
        # mensaje_error = 'TEST pago es gna %s' % (self.payment_ids[0].journal_id)
        # _logger.warning(mensaje_error)
        # raise ValidationError(mensaje_error)
        for rec in self:
            if not rec.name:
                if rec.talonario_id:
                    if rec.talonario_id.numero_actual <= rec.talonario_id.hasta:
                        rec.ultimo_numero = rec.talonario_id.numero_actual
                    else:
                        raise ValidationError(
                            'El talonario del recibo ya no posee numeros disponibles , Favor contactar con el Jefe de Credito y Cobranza')
                else:
                    rec.ultimo_numero = False
            else:
                rec.ultimo_numero = rec.talonario_id.numero_actual

    def unlink(self):
        for rec in self:
            if rec.pagos_facturas_ids:
                raise ValidationError("Para poder eliminar el recibo favor elimine sus lineas de Factura primeramente.")
            if rec.payment_ids:
                raise ValidationError("Para poder eliminar el recibo favor elimine sus lineas de COBROS primeramente.")
            if rec.state != 'borrador':
                raise ValidationError("Solo se puede elmininar un recibo en estado  Borrador")
            return super(models.Model, self).unlink()

    def post_caja_recibo(self):

        # if not self.env.user.cajero:
        #     raise ValidationError('No posee perfil de cobrador o cajero. Verifique con el administrador')
        for rec in self:
            if rec.talonario_id.requiere_caja:
                cajas=self.env['ruc.cajas'].search([('state','=','abierto'),('fondo_fijo','=',False)])


                caja_id=cajas.filtered(lambda r:r.usuarios_asignados.filtered(lambda r: r == self.env.user))

                if not caja_id:
                    raise ValidationError('El cobrador %s No posee caja abierta. ' % self.env.user.name)



                valores = list()
                cobro_efectivo = 0
                cobro_banco = 0
                fecha_diferido = None
                cobro_retencion_nro = None
                cobro_retencion_monto = 0
                cobro_cheque_cant = 0
                cobro_cheque_visual = 0

                for cobro in self.payment_ids:

                    if cobro.journal_id.tipo_reporte == 'efectivo':
                        cobro_efectivo = cobro.amount
                    # if cobro.env.user.cobrador:
                    if cobro.journal_id.tipo_reporte == 'retencion':  # retencion su id es 10
                        cobro_retencion_nro = cobro.numero_transaccion
                        cobro_retencion_monto = cobro.amount

                    # elif cobro.journal_id.type == 'cash':
                    #     cobro_efectivo = cobro.amount
                    # elif cobro.journal_id.id == self.env.user.diario_caja_usd.id:
                    #     cobro_efectivo = cobro.amount
                    elif cobro.journal_id.tipo_reporte == 'transferencia':
                        cobro_banco = cobro.amount
                    elif cobro.journal_id.tipo_reporte == 'cheques':
                        cobro_cheque_cant = cobro.amount
                        cobro_cheque_visual += cobro.amount
                        # if cobro.tipo_de_cheque_recibo == 'deferred':
                        #     fecha_diferido = cobro.fecha_cheque_diferido
                        # else:
                        fecha_cheque=cobro.fecha_cheque_recibo
                        fecha_diferido = cobro.fecha_cheque_diferido
                        # if self.env.user.cajero or self.env.user.cobrador:
                        for ch in cobro.received_third_check_ids:
                            # raise ValidationError ('aaa %s' % ch.number)
                            valores.append(ch.id)

                    # if self.env.user.cajero or self.env.user.cobrador:
                    caja = caja_id.id

                    # movi = self.env['ruc.caja.detalle'].search([('recibo_id','=',self.id)])
                    # if movi:
                    #     raise ValidationError('Aqui esta el error 1')
                    movi_obj = self.env['ruc.caja.detalle']

                    movi_vals = {
                        'caja_id': caja,
                        'name': 'Cobro Recibo ' + str(self.name) ,
                        'tipo': 'ingreso',
                        'currency_id': self.currency_id.id,
                        'monto': self.amount,
                        'cliente': self.partner_id.id,
                        'cobro_efectivo': cobro_efectivo,
                        'cobro_cheque': [(6, 0, valores)],
                        'cobro_cheque_cant': cobro_cheque_cant,
                        'cobro_cheque_visual': cobro_cheque_visual,
                        'cobro_retencion_nro': cobro_retencion_nro,
                        'cobro_retencion_monto': cobro_retencion_monto,
                        'cobro_transferencia': cobro_banco,
                        'total': self.amount,
                        'recibo_id': self.id
                    }
                    movi_obj.create(movi_vals)

    def agregar_punto_de_miles2(self, numero):
        numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(numero))), 3)])[::-1]
        return numero_con_punto
    
    @api.model
    def numero_formateado(self, numero):
        return self.agregar_punto_de_miles2(numero)

class PagosFactura(models.Model):
    _name = 'account.pago.factura'

    name = fields.Char(string="", readonly=True)
    invoice_id = fields.Many2one('account.move', 'Factura')
    move_line_id = fields.Many2one('account.move.line', 'Apunte')
    amount = fields.Float(string="Monto Nota Credito")
    recibo_id = fields.Many2one('account.recibo')
    fecha_pago = fields.Date(related='recibo_id.fecha')
    currency_invoice = fields.Many2one('res.currency', compute='get_move_data')
    moneda_company = fields.Boolean(compute="_get_recibo_currency")
    partner_id = fields.Many2one('res.partner', related='recibo_id.partner_id')
    currency_id = fields.Many2one('res.currency', related='invoice_id.currency_id')
    invoice_date = fields.Date(compute='get_move_data')
    nro_factura = fields.Char()
    amount_total = fields.Monetary()
    residual = fields.Monetary(store=True)
    monto = fields.Float(string="Pago")
    monto_gs = fields.Float(string="Pago Gs.")
    viene_del_pago = fields.Boolean(default=False)
    paso_por_el_pago = fields.Integer(default=0)
    retencion = fields.Boolean()
    account_receivable = fields.Many2one('account.account', string="Cuenta a Cobrar", compute="get_receivable_account")

    @api.onchange('invoice_id', 'move_line_id')
    def check_receivable_account(self):
        for rec in self:
            cuenta = None
            if rec.invoice_id:
                cuenta = rec.recibo_id.pagos_facturas_ids.mapped('invoice_id').mapped('line_ids').mapped(
                    'account_id').filtered(lambda r: r.account_type == 'asset_receivable')
                # cuentas = rec.orden_pagos_facturas_ids.mapped('invoice_id').mapped('line_ids').mapped(
                #     'account_id').filtered(lambda r: r.internal_type == 'payable')
                if len(cuenta) > 1:
                    raise ValidationError(
                        'No puede cobrar en una misma recibo facturas con diferentes cuentas a Cobrar')
            elif rec.move_line_id:
                cuenta = rec.recibo_id.pagos_facturas_ids.mapped('move_line_id').mapped('account_id')
                # cuentas = rec.orden_pagos_facturas_ids.mapped('invoice_id').mapped('line_ids').mapped(
                #     'account_id').filtered(lambda r: r.internal_type == 'payable')
                if len(cuenta) > 1:
                    raise ValidationError(
                        'No puede cobrar en un mismo recibo deudas con diferentes cuentas a Cobrar')

    @api.depends('invoice_id', 'move_line_id')
    def get_receivable_account(self):
        for rec in self:
            cuenta = None
            if rec.invoice_id:
                cuenta = rec.invoice_id.mapped('line_ids').mapped('account_id').filtered(
                    lambda r: r.account_type == 'asset_receivable')
                if cuenta:
                    cuenta = cuenta[0]
            elif rec.move_line_id:
                cuenta = rec.move_line_id.account_id
            rec.account_receivable = cuenta

    @api.onchange('invoice_id', 'move_line_id')
    def get_move_data(self):
        for rec in self:
            rec.invoice_date = False
            rec.currency_invoice = False
            if rec.invoice_id:
                rec.invoice_date = rec.invoice_id.invoice_date
                rec.currency_invoice = rec.invoice_id.currency_id
            elif rec.move_line_id:
                rec.invoice_date = rec.move_line_id.date_maturity
                rec.currency_invoice = rec.move_line_id.currency_id

    @api.depends('currency_id')
    def _get_recibo_currency(self):
        for rec in self:
            if rec.recibo_id:
                if rec.recibo_id.currency_id != self.env.company.currency_id:
                    rec.moneda_company = False
                else:
                    rec.moneda_company = True

    @api.onchange('monto')
    @api.constrains('monto')
    def verificar_monto(self):
        for rec in self:
            if not rec.id:
                if rec.monto != rec.residual:
                    rec.amount = rec.monto

            if rec.currency_id == rec.invoice_id.currency_id:
                if rec.invoice_id.move_type == 'out_invoice':
                    if rec.monto > rec.residual:
                        raise ValidationError('El monto no puede ser mayor al saldo de la factura')
                elif rec.invoice_id.move_type == 'out_refund':
                    if rec.monto < rec.residual:
                        raise ValidationError('El monto no puede ser mayor al saldo de la nota de credito')

    def set_datos_iniciales(self):
        for rec in self:
            if rec.move_line_id:
                if rec.move_line_id.amount_currency != 0:
                    rec.monto = rec.move_line_id.amount_residual_currency
                    rec.amount = rec.move_line_id.amount_residual_currency
                    rec.residual = rec.move_line_id.amount_residual_currency
                    rec.amount_total = abs(rec.move_line_id.amount_currency)
                else:
                    rec.monto = rec.move_line_id.amount_residual
                    rec.amount = rec.move_line_id.amount_residual
                    rec.residual = rec.move_line_id.amount_residual
                    rec.amount_total = abs(rec.move_line_id.balance)
            elif rec.invoice_id:
                if rec.invoice_id.move_type in ('out_invoice', 'in_invoice'):
                    rec.monto = rec.invoice_id.amount_residual
                    rec.amount = rec.invoice_id.amount_residual
                    rec.residual = rec.invoice_id.amount_residual
                    rec.amount_total = rec.invoice_id.amount_total
                else:
                    rec.monto = rec.invoice_id.amount_residual_signed
                    rec.amount = rec.invoice_id.amount_residual_signed
                    rec.residual = rec.invoice_id.amount_residual_signed
                    rec.amount_total = rec.invoice_id.amount_total_signed

    @api.onchange('invoice_id', 'move_line_id')
    def _set_pago(self):
        for rec in self:
            if not rec.id:
                rec.set_datos_iniciales()
            else:
                if rec.invoice_id:
                    if rec.recibo_id.state == 'borrador':
                        if rec.monto != rec.invoice_id.amount_residual:
                            rec.amount = rec.monto
                    if rec.invoice_id.move_type in ('out_invoice', 'in_invoice'):
                        rec.residual = rec.invoice_id.amount_residual
                        rec.amount_total = rec.invoice_id.amount_total
                    else:
                        if rec.currency_id != rec.invoice_id.currency_id:
                            if rec.currency_id != self.env.company.currency_id:
                                coti = self.env['res.currency.rate'].search(
                                    [['name', '=', rec.fecha_pago], ['currency_id', '=', rec.currency_invoice.id]])
                                if not coti:
                                    raise ValidationError(
                                        'aNo se encuentra cotizacion %s para el dia %s . Verifique que la cotizacion se encuentre cargada ' % (
                                            rec.currency_id.name, str(
                                                rec.fecha_pago)))
                            if rec.invoice_id.currency_id != self.env.company.currency_id:
                                coti = self.env['res.currency.rate'].search(
                                    [['name', '=', rec.fecha_pago],
                                     ['currency_id', '=', rec.invoice_id.currency_id.id]])
                                if not coti:
                                    raise ValidationError(
                                        'No se encuentra cotizacion %s para el dia %s . Verifique que la cotizacion se encuentre cargada ' % (
                                            rec.invoice_id.currency_id.name, str(
                                                rec.fecha_pago)))
                            residual_currency = rec.invoice_id.currency_id.with_context(date=rec.fecha_pago).compute(
                                rec.invoice_id.amount_residual, rec.currency_id)
                elif rec.move_line_id:
                    if rec.recibo_id.state == 'borrador':
                        if rec.monto != rec.move_line_id.amount_residual_currency:
                            rec.amount = rec.monto
                        rec.amount_total = abs(rec.move_line_id.amount_currency or rec.move_line_id.balance)
                    else:
                        if rec.currency_id != rec.move_line_id.currency_id:
                            if rec.currency_id != self.env.company.currency_id:
                                coti = self.env['res.currency.rate'].search(
                                    [['name', '=', rec.fecha_pago], ['currency_id', '=', rec.currency_invoice.id]])
                                if not coti:
                                    raise ValidationError(
                                        'aNo se encuentra cotizacion %s para el dia %s . Verifique que la cotizacion se encuentre cargada ' % (
                                            rec.currency_id.name, str(
                                                rec.fecha_pago)))
                            if rec.move_line_id.currency_id != self.env.company.currency_id:
                                coti = self.env['res.currency.rate'].search(
                                    [['name', '=', rec.fecha_pago],
                                     ['currency_id', '=', rec.move_line_id.currency_id.id]])
                                if not coti:
                                    raise ValidationError(
                                        'No se encuentra cotizacion %s para el dia %s . Verifique que la cotizacion se encuentre cargada ' % (
                                            rec.move_line_id.currency_id.name, str(
                                                rec.fecha_pago)))
                            residual_currency = rec.move_line_id.currency_id.with_context(date=rec.fecha_pago).compute(
                                rec.move_line_id.amount_residual_currency, rec.currency_id)
                if rec.monto == 0:
                    rec.monto = residual_currency
                if rec.amount == residual_currency or rec.amount == 0:
                    rec.amount = residual_currency
                if rec.monto != residual_currency and rec.monto != 0:
                    rec.amount = rec.monto
                rec.residual = rec.invoice_id.amount_residual
                rec.amount_total = rec.invoice_id.amount_total

    def verificar_amount(self):
        if self.invoice_id.move_type in ('out_refund', 'in_refund'):
            pass
        else:
            self.amount = self.monto

    def actualizar_amount(self):
        if self.invoice_id.move_type in ('out_invoice', 'in_invoice'):
            if self.monto == self.invoice_id.amount_residual:
                self.amount = self.invoice_id.amount_residual
            else:
                if self.retencion:
                    payment_retencion = self.env['account.payment'].search(
                        [('recibo_id', '=', self.recibo_id.id), ('factura_retenida', '=', self.invoice_id.id),
                         ('state', '=', 'posted')])
                    print(payment_retencion)
                    if len(payment_retencion) == 1:
                        monto_retencion = payment_retencion.amount
                        suma = self.invoice_id.amount_residual + monto_retencion
                        if suma <= self.monto:
                            self.amount = self.invoice_id.amount_residual
                        else:
                            self.amount = self.monto - monto_retencion
                    else:
                        self.amount = self.invoice_id.amount_residual


                else:
                    self.amount = self.monto
        else:
            if self.monto == self.invoice_id.amount_residual_signed:
                self.amount = self.invoice_id.amount_residual_signed
            else:
                self.amount = self.monto
