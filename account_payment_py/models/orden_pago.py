# -*- coding: UTF-8 -*-

from odoo import fields, api, models
from odoo.exceptions import ValidationError
import time
from datetime import datetime, date, time, timedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

import logging

_logger = logging.getLogger(__name__)


class OrdenPago(models.Model):
    _name = 'account.orden.pago'
    _order = "id desc"

    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    #
    # def create(self,vals):
    #
    #
    #
    #     res = super(OrdenPago, self).create(vals)crea
    #
    #     for asd in res:
    #         asd.talonario_id.numero_actual = asd._get_last_number()
    #         if (asd.talonario_id.numero_actual-1 )== asd.talonario_id.hasta:
    #             asd.talonario_id.es_ultimo_nro=True
    #
    #     return res



    name = fields.Char(string="Nro. de Orden Pago", readonly=True, copy=False)
    state = fields.Selection(
        [('borrador', 'Borrador'), ('pendiente', 'Pendiente'), ('confirmado', 'Confirmado'), ('anulado', 'Anulado')],
        default='borrador', track_visibility='onchange')
    
    secuencia = fields.Integer()
    fecha = fields.Date(string="Fecha", required=True, default=fields.Date.today(), track_visibility="onchange")
    tipo = fields.Selection(selection=[
        ('move', 'Por facturas'),
        ('move_line', 'Por apuntes')
    ], string="Tipo", default="move")

    currency_id = fields.Many2one('res.currency', string="Moneda", track_visibility="onchange")
    amount = fields.Monetary(currency_field='currency_id', string="Cantidad a pagar", compute="calcular_monto")
    saldo = fields.Monetary(currency_field="currency_id", string="Saldo", compute="_calcular_saldo")
    total_pagos = fields.Monetary(compute="_calcular_pagos", currency_field="currency_id", string="Total Pagos",
                                  readonly=True)
    diferencia_cambio = fields.Float(string="Diferencia de cambio")
    diferencia = fields.Selection([('utilidad', 'Utilidad'), ('a_cuenta', 'A Favor del Cliente/Anticipo')],
                                  string="Guardar Diferencia Como:")

    obs = fields.Html(string="Observaciones", help="Nombre que se utilizará en los apuntes contables")
    existe_pago_gs_extranjero = fields.Boolean(compute="_verificar_lineas", default=False)


    partner_id = fields.Many2one('res.partner', 'Proveedor', required=True, track_visibility="onchange")
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    
    orden_pagos_facturas_ids = fields.One2many('account.orden.pago.factura', 'orden_pago_id')

    diario_diferencia = fields.Many2one('account.journal', 'Diario de diferencia de cambio')
    cuenta_diferencia = fields.Many2one('account.account', 'Cuenta Diferencia de cambio')
    move_diferencia_id = fields.Many2one('account.move', 'Asiento de diferencia cambiaria')

    move_id = fields.Many2one('account.move', string="Asiento de Diferencia")
    payment_ids = fields.One2many('account.payment', 'orden_pago_id', string="Pagos", track_visibility="onchange")
    motivo_anulacion = fields.Many2one('ruc.motivo.anulacion', string='Motivo de Anulacion')
    check_ids = fields.One2many('account.check', 'orden_pago_id', string="Cheques")
    
    
    reconciled_invoice_ids = fields.Many2many('account.move', string="Facturas", compute='_get_facturas')
    total_facturas_adeudadas = fields.Monetary(currency_field="currency_id", string="Total de facturas abiertas",
                                               compute='_calcular_facturas_adeudadas')
    
    method_id = fields.Integer(compute='get_manual_method_out')
    get_parcial = fields.Boolean(string="Posee pago parcial", compute='has_partial_payment')
    moneda_company = fields.Boolean(compute="_get_orden_pago_currency")
    recibo_proveedor = fields.Char(string="Nro. Recibo Proveedor", track_visibility="onchange")


    
    company_id = fields.Many2one('res.company', 'Company', required=True,
                                 default=lambda self: self._get_default_company())
    usuario = fields.Many2one('res.users', default=lambda self: self._get_default_user(), track_visibility="onchange")
    mostrar_datos_bancarios = fields.Boolean(
        compute="_compute_mostrar_datos_bancarios",
        store=False
    )

    def _get_default_user(self):
        return self.env.user.id
        
    def set_op_code(self):
        for rec in self:
            self.name = self.env['ir.sequence'].get('orden_pago.sequence')

    @api.depends('orden_pagos_facturas_ids.monto')
    def has_partial_payment(self):
        for rec in self:
            get_parcial = False
            for lineas in rec.orden_pagos_facturas_ids:
                try:
                    if lineas.monto != lineas.residual:
                        get_parcial = True
                except:
                    get_parcial = False
            rec.get_parcial = get_parcial

    @api.onchange('tipo')
    def vaciar_lineas(self):
        for rec in self:
            rec.orden_pagos_facturas_ids.unlink()
            rec.orden_pagos_facturas_ids = False

    def _get_facturas(self):
        for rec in self:
            rec.reconciled_invoice_ids = rec.orden_pagos_facturas_ids.mapped('invoice_id.id')

    def retornar_asignacion(self):
        view = self.env.ref('account_payment_py.wizard_asignacion_facturas')
        invoices = self.env['account.move'].search([('no_ver_factura_pago', '=', False), ('state', '=', 'posted'),
                                                    ('payment_state', 'in', ('not_paid', 'in_payment', 'partial')),
                                                    ('partner_id', 'child_of', self.partner_id.id),
                                                    # ('account_analytic_id', '=', self.account_analytic_id.id),
                                                    ('move_type', '=', 'in_invoice')], order='invoice_date asc',
                                                   limit=10)
        if len(invoices) > 0:
            wiz = self.env['account_payment_py.wizard_asignacion'].create({'invoice_ids': [(6, 0, invoices.ids)],
                                                                           'op_id': self.id,
                                                                           'partner_id': self.partner_id.id,
                                                                           'currency_id': self.currency_id.id})
        else:
            wiz = self.env['account_payment_py.wizard_asignacion'].create({'op_id': self.id})

        return {
            'name': 'Asignar facturas',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account_payment_py.wizard_asignacion',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }

    def eliminar_asignacion(self):
        if self.orden_pagos_facturas_ids:
            for f in self.orden_pagos_facturas_ids:
                f.invoice_id.no_ver_factura_pago = False
            self.orden_pagos_facturas_ids.unlink()

    @api.onchange('currency_id')
    def verificar_cambio_moneda(self):
        """
        Funcion donde al cambiar la moneda del recibo setea en None los campos
        de diferencia de precios
        :return:
        """
        for rec in self:
            if rec.orden_pagos_facturas_ids:
                for factu in rec.orden_pagos_facturas_ids:
                    factu.monto_gs = 0
                rec.diferencia_cambio = 0
                rec.diario_diferencia = None
                rec.cuenta_diferencia = None
                if rec.currency_id == self.env.company.currency_id:
                    rec.existe_pago_gs_extranjero = False

    @api.depends('payment_ids.monto_moneda_pago')
    def _verificar_lineas(self):
        suma = 0
        for rec in self:

            if any(pay.monto_moneda_pago != 0 for pay in rec.payment_ids):
                if rec.currency_id != self.env.company.currency_id:
                    rate = self.env['res.currency.rate'].search(
                        [('currency_id', '=', rec.currency_id.id), ('name', '=', rec.fecha)])
                    if not rate:
                        raise ValidationError('No existe cotizacion para la fecha del recibo')
                    else:
                        rec.existe_pago_gs_extranjero = True
                        total_mon = rec.total_pagos * rate.set_venta
                    for f in rec.payment_ids:
                        if f.monto_moneda_pago > 0:
                            suma += f.monto_moneda_pago
                        else:
                            suma += f.amount * rate.set_venta

                    suma = suma - total_mon
                    rec.diferencia_cambio = suma
                    journal = self.env['account.journal'].search([('exchange_rate_journal', '=', True), (
                        'company_id', '=', self.env.company.id)])

                    if len(journal) > 0:
                        rec.diario_diferencia = journal[0]
                        cuenta_ganancia = self.env['res.config.settings'].sudo().search([], limit=1,
                                                                                        order="id desc").income_currency_exchange_account_id
                        cuenta_perdida = self.env['res.config.settings'].sudo().search([], limit=1,
                                                                                       order="id desc").expense_currency_exchange_account_id
                        if rec.diferencia_cambio > 0:
                            rec.cuenta_diferencia = cuenta_ganancia
                        elif rec.diferencia_cambio < 0:
                            rec.cuenta_diferencia = cuenta_perdida
                else:
                    rec.diferencia_cambio = 0
                    rec.existe_pago_gs_extranjero = False
            else:
                rec.diferencia_cambio = 0
                rec.existe_pago_gs_extranjero = False

    @api.depends('currency_id')
    def _get_orden_pago_currency(self):
        for rec in self:
            if rec.currency_id != self.env.company.currency_id:
                rec.moneda_company = False
            else:
                rec.moneda_company = True

    @api.onchange('fecha')
    def agregar_al_context(self):
        if self.fecha:
            self = self.with_context(fecha=self.fecha)

    @api.depends('partner_id')
    def get_manual_method_out(self):
        for rec in self:
            rec.method_id = self.env.ref('account.account_payment_method_manual_out').id

    @api.depends('total_pagos', 'amount')
    def _calcular_saldo(self):
        for rec in self:
            rouding = rec.currency_id.decimal_places
            rec.saldo = round((rec.amount - rec.total_pagos), rouding)

    @api.depends('payment_ids')
    def _calcular_pagos(self):
        cuentas = self.get_invoices_move_accounts()
        for rec in self:
            if rec.payment_ids:
                for p in rec.payment_ids:
                   if not p.journal_id.type == 'retencion':
                        rec.total_pagos += p.amount
            else:
                rec.total_pagos = 0

    def get_invoices_move_accounts(self):
        for rec in self:
            cuentas_dict = {}
            tot_cuen = 0
            cuentas = rec.orden_pagos_facturas_ids.mapped('account_payable')
            if len(cuentas) > 0:
                return cuentas[0]
            else:
                return cuentas

    @api.depends('reconciled_invoice_ids')
    def _calcular_facturas_adeudadas(self):
        for rec in self:
            if rec.reconciled_invoice_ids:
                total = 0
                for f in rec.reconciled_invoice_ids:
                    total += f.residual
                rec.total_facturas_adeudadas = total

    @api.constrains('payment_ids')
    def verificar_pago(self):
        for rec in self:
            if rec.payment_ids:
                pagos_distintos = rec.payment_ids.filtered(lambda record: record.partner_id != rec.partner_id)
                pagos_distintas_monedas = rec.payment_ids.filtered(lambda record: record.currency_id != rec.currency_id)
                if pagos_distintos:
                    raise ValidationError(
                        'No pueden crearse Orden de Pagos, con pagos relacionados a empresas distintas a la detallada en la Orden de Pago')
                if pagos_distintas_monedas:
                    raise ValidationError(
                        'No pueden crearse Orden de Pagos, con pagos relacionados a monedas distitnas a la detallada en la Orden de Pago %s' % pagos_distintas_monedas)

    @api.depends('orden_pagos_facturas_ids')
    def calcular_monto(self):
        for rec in self:
            rec.amount = 0
            for f in rec.orden_pagos_facturas_ids:
                try:
                    if f.amount_total < 0:
                        rec.amount += f.monto
                        if rec.currency_id != self.env.company.currency_id and rec.diario_diferencia:
                            rec.amount = rec.monto_gs
                        else:
                            rec.amount += f.monto
                    else:
                        rec.amount += f.monto
                except:
                    rec.amount += f.monto

    def _get_default_company(self):
        return self.env.company.id

    def pasar_a_pendiente(self):
        if not self.name:
            self.name = self.env['ir.sequence'].get('orden_pago.sequence')
        self.state = 'pendiente'

    def pendiente_a_borrador(self):
        if self.state == 'pendiente':
            self.state = 'borrador'

    def confirmar_orden_pago(self):

        if self.saldo < 0:

            return {
                'type': 'ir.actions.act_window',
                'res_model': 'diferencia.op',
                'context': {'default_op_id': self.id},
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
            }
        elif self.saldo > 0:
            raise ValidationError(
                'Hay una diferencia entre el Monto de la Factura y el Cobro, Favor fijarse en el campo "DIFERENCIA" debe ser igual a 0')
        else:
            self.set_confirmado()



    def set_confirmado(self):
        print("Entra en set Confirmado account_payment_py")
        domain_pago = ([('account_type', '=', 'liability_payable')])
        cheques = list()
        to_reconcile = self.env['account.move.line']
        self.check_ids = [(5,)]
        tiene_factura = False
        #_logger.warning('SELF DE PAYMENT IDS %s', self)
        if self.payment_ids and self.orden_pagos_facturas_ids:
            #_logger.warning('PAYMENT IDS %s', self.payment_ids)
            if not self.name:
                self.name = self.env['ir.sequence'].get('orden_pago.sequence')
            if any(pay.asignar_factura != False for pay in self.payment_ids):
                tiene_factura = True
            #_logger.warning('TIENE FACTURA??? %s', tiene_factura)
            if self.tipo_retencion == 'total' or self.tipo_retencion == 'parcial':
                #_logger.warning('RETENCION')
                try:
                    diario_retencion_pago = self.env.company.retencion_iva_journal_id
                    diario_retencion_cobro = self.env.company.retencion_iva_retenido_journal_id
                    diario_retencion_renta = self.env.company.retencion_renta_journal_id
                    diario_retencion_ley = self.env.company.retencion_ley_journal_id
                    domain = self.payment_ids.filtered(
                        lambda x: x.journal_id not in (
                            diario_retencion_pago, diario_retencion_cobro, diario_retencion_renta,
                            diario_retencion_ley)).filtered(
                        lambda x: x.asignar_factura == False)
                except:
                    domain = self.payment_ids.filtered(
                        lambda x: x.asignar_factura == False)
            else:
                domain = self.payment_ids
                #_logger.warning('DOMAIN ES %s', domain)
            # _logger.info('parcial')
            # _logger.info(self.get_parcial)
            if tiene_factura:
                domain = self.payment_ids.filtered(lambda x: x.asignar_factura == False and x.state == 'draft')
                #_logger.warning('DOMAIN SOLO %s', domain)
                domain_factura = self.payment_ids.filtered(lambda x: x.asignar_factura == True and x.state == 'draft')
                #_logger.warning('DOMAIN FACTURA %s', domain_factura)
                for p in domain_factura:
                    #_logger.warning('P IN DOMAIN %s', p)
                    diario = p.journal_id
                    pago = p.amount
                    #_logger.warning('PAGO %s', pago)
                    #_logger.warning('RECONCILED ES %s', p.reconciled_invoice_ids.mapped('id'))
                    # facturas = self.orden_pagos_facturas_ids.filtered(
                    #     lambda r: r.invoice_id.amount_residual > 0 and r.invoice_id.move_type not in (
                    #         'out_refund', 'in_refund') and r.invoice_id.id in p.reconciled_invoice_ids.mapped('id')
                    # ).sorted(key=lambda r: r.residual)
                    facturas = self.orden_pagos_facturas_ids.filtered(
                        lambda r: r.invoice_id.amount_residual > 0 and r.invoice_id.move_type not in (
                            'out_refund', 'in_refund')).sorted(key=lambda r: r.residual)
                    #_logger.warning('FASCADASFASDF %s', facturas)
                    for i in facturas.sorted(key=lambda r: r.monto, reverse=True):
                        pago = i.monto
                        #_logger.warning('FACTURA PROCESADA %s', i.invoice_id.nro_factura)
                        if pago > 0:
                            if not i.invoice_id.move_type in ('out_refund', 'in_refund'):
                                #_logger.warning('FACTURA %s', i.invoice_id.nro_factura)
                                i.amount -= pago
                                i.invoice_id.monto_a_pagar = pago
                                # raise ValidationError('TEST %s', i.invoice_id.id)
                                #_logger.warning('AMOUNT RESIDUAL ANTES %s', i.invoice_id.amount_residual)
                                i.invoice_id.amount_residual = i.residual
                                #i.invoice_id.amount_residual -= pago
                                #_logger.warning('AMOUNT RESIDUAL DESPUES %s', i.invoice_id.amount_residual)
                                pago = 0
                                i.viene_del_pago = True
                                i.paso_por_el_pago = 1
                            to_reconcile += (i.invoice_id.line_ids.filtered_domain(domain_pago))
                            #_logger.warning('TO RECONCILE JUSTO DESPUES DEL RESIDUAL %s', to_reconcile)
                    p.action_post()
                    payment_lines = p.line_ids.filtered_domain(domain_pago)
                    #_logger.warning('payment_lines %s', payment_lines)
                    for account in payment_lines.account_id:
                        (payment_lines + to_reconcile) \
                            .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                            .with_context(op=self, has_partial=self.get_parcial).reconcile()
                        #_logger.warning('DESPUES DE RECON')
                    p.orden_pago_id = self.id
                    # p.action_post
            for p in domain.sorted(key=lambda r: r.amount, reverse=True):
                diario = p.journal_id
                #_logger.warning('P ES %s', p._context)
                pago = p.amount
                #_logger.warning('PAGO %s', pago)
                to_reconcile = self.env['account.move.line']
                facturas = self.orden_pagos_facturas_ids.filtered(
                    lambda r: r.invoice_id.amount_residual > 0 and r.invoice_id.move_type not in (
                        'out_refund', 'in_refund')).sorted(key=lambda r: r.residual)
                _#logger.warning('FACTURAS DE ORDEN %s', facturas)

                _#logger.info('es parcial')
                #_logger.info(self.get_parcial)
                for i in facturas.sorted(key=lambda r: r.residual, reverse=True):
                    #_logger.warning('LINEA FACT %s', i._context)
                    if pago > 0:
                        if not i.invoice_id.move_type in ('out_refund', 'in_refund'):
                            if i.amount == 0:
                                i.verificar_amount()
                                continue
                            elif pago <= i.amount:
                                i.amount -= pago
                                i.invoice_id.monto_a_pagar = pago
                                p.reconciled_invoice_ids = [(4, i.invoice_id.id)]
                                #_logger.warning('FACTURA A APLICAR %s', i.invoice_id.nro_factura)
                                #_logger.warning('RESIDUAL ANTES DE MODIF %s', i.invoice_id.amount_residual)
                                i.invoice_id.amount_residual-=pago
                                #_logger.warning('RESIDUALLLLLLL %s', i.invoice_id.nro_factura)
                                #_logger.warning('RESIDUALLLLLLL %s', i.invoice_id.amount_residual)
                                #_logger.warning('RESIDUAL LINEA %s', i.residual)
                                # raise ValidationError('id: %s monto: %s' % (i.invoice_id.id, i.invoice_id.amount_residual))
                                pago = 0
                                i.viene_del_pago = True
                                i.paso_por_el_pago = 1
                            else:
                                pago -= i.amount
                                i.invoice_id.monto_a_pagar = i.amount
                                p.reconciled_invoice_ids = [(4, i.invoice_id.id)]
                                # i.invoice_id.amount_residual-=i.amount
                                i.amount = 0
                                i.viene_del_pago = True
                                i.paso_por_el_pago = 1
                            to_reconcile += (i.invoice_id.line_ids.filtered_domain(domain_pago))
                            #_logger.warning('TO RECONCILE EN SET CONFIRMADO ES %s', to_reconcile)
                    else:
                        break
                # _logger.info('parcial')
                # _logger.info(self.get_parcial)
                apuntes = self.orden_pagos_facturas_ids.filtered(
                    lambda r: r.move_line_id.amount_residual != 0)
                #_logger.warning('APUNTES ES %s', apuntes)
                aux = 0
                for i in apuntes.sorted(key=lambda r: r.amount, reverse=True):
                    if pago > 0:
                        if i.amount == 0:
                            i.verificar_amount()
                            continue
                        elif pago <= i.amount:
                            i.amount -= pago
                            i.move_line_id.monto_a_pagar = pago
                            # i.invoice_id.amount_residual-=pago
                            pago = 0
                            i.viene_del_pago = True
                            i.paso_por_el_pago = 1
                        else:
                            aux += i.monto
                            pago -= i.amount
                            i.move_line_id.monto_a_pagar = i.amount
                            i.amount = 0
                            i.viene_del_pago = True
                            i.paso_por_el_pago = 1
                        to_reconcile += (i.move_line_id.filtered_domain(domain_pago))
                    else:
                        break
                moneda_company = self.env.company.currency_id

                cuentas = self.get_invoices_move_accounts()
                # self.currency_id = moneda_anterior
                # self.amount = amount_anterior
                p.action_post()
                #### en caso de que el payment tenga moneda alternativa GS y la OP sea en dolares se actualiza manualmente el amount_currency en USD
                # TODO: corregir aca ya que actualizar_monto_moneda no se define en ningun lugar de la localizacion en la V17
                # actualmente no se activa el segundo if ya que moneda_pago no se pasa en la vista
                if p.moneda_pago:
                    if (self.currency_id == moneda_company) and (p.moneda_pago != moneda_company):
                        #_logger.warning('moneda %s', p.currency_id)
                        p.actualizar_monto_moneda()
                p.with_context(cuenta=cuentas)._compute_destination_account_id()
                payment_lines = p.line_ids.filtered_domain(domain_pago)
                _logger.warning('PAYMENT LINES %s', payment_lines)
                for account in payment_lines.account_id:
                    _logger.warning('ACCOUNT %s', account)
                    _logger.warning('PAYMENT + TO RECONCILE %s', (payment_lines + to_reconcile))
                    (payment_lines + to_reconcile) \
                        .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]) \
                        .with_context(op=self, has_partial=self.get_parcial).reconcile()
                    _logger.warning('RECONCILIACION EJECUTADA EN %s', account)
                p.orden_pago_id = self.id
            if pago > 0:
                if self.saldo != 0:
                    if self.saldo < 0:
                        self.asiento_utilidad(pago, diario, self.currency_id)
                        _logger.info(f"asiento utilidad funcion")
            self.state = 'confirmado'
            if self.diferencia_cambio != 0:
                self._crear_diferencia_cambio()
            for p in self.payment_ids:
                if p.numero_cheque_pago:
                    cheque_propio = self.env['account.check'].search(
                        [('number', '=', p.numero_cheque_pago),
                         ('checkbook_id', '=', p.checkbook_id.id)])

                    if p.monto_moneda_pago > 0:
                        monto_cheque = p.monto_moneda_pago
                        currency_cheque = p.moneda_pago
                    else:
                        monto_cheque = p.amount
                        currency_cheque = p.currency_id
                    if not cheque_propio:
                        vals = {
                            'number': p.numero_cheque_pago,
                            'amount': monto_cheque,
                            'issue_date': p.fecha_cheque_pago,
                            'payment_date': p.fecha_cheque_diferido,
                            'checkbook_id': p.checkbook_id.id,
                            'voucher_id': p.id,
                            'currency_id': currency_cheque.id,
                            'orden_pago_id': self.id,
                            'state': 'draft',
                            'type': 'issue_check',
                            'comentario': p.observaciones

                        }
                        cheque = self.env['account.check'].create(vals)
                        cheques.append(cheque.id)
                        self.check_ids = [(6, 0, cheques)]
                    else:
                        # raise ValidationError ('No se puede duplicar numero de Cheque.')
                        if cheque_propio.orden_pago_id.id and cheque_propio.orden_pago_id.id != self.id:
                            raise ValidationError(
                                'El cheque  ya esta asignado a otra orden de pago %s favor verificar ' % cheque_propio.orden_pago_id.name)
                        vals = {
                            'number': p.numero_cheque_pago,
                            'amount': monto_cheque,
                            'issue_date': p.fecha_cheque_pago,
                            'payment_date': p.fecha_cheque_diferido,
                            'checkbook_id': p.checkbook_id.id,
                            'voucher_id': p.id,
                            'currency_id': currency_cheque.id,
                            'orden_pago_id': self.id,
                            'state': 'draft',
                            'type': 'issue_check',
                            'comentario': p.observaciones
                        }
                        cheque_propio.write(vals)
        else:
            raise ValidationError('No tiene asociado ninguna "Factura o Cobro" a la Orden de Pago')

        for payments in self.payment_ids:
            payments.name = 'Orden de Pago Nro: ' + self.name
        for i in self.orden_pagos_facturas_ids:
            i.viene_del_pago = False
            i.paso_por_el_pago = 0

    def asiento_utilidad(self, pago, diario, moneda):
        if pago > 0:
            fecha = self.fecha
            monto_pago = pago
            if moneda != self.env.company.currency_id:
                rate = self.env['res.currency.rate'].search([['name', '=', fecha], ['currency_id', '=', moneda.id]])
                pago = pago * rate.set_venta
            vals = self.get_vals(pago, fecha, diario, monto_pago, moneda)

            # extraemos los vals
            move_vals = vals.get('move_vals', {})
            debit_line_vals = vals.get('debit_line_vals', {})
            credit_line_vals = vals.get('credit_line_vals', {})
            # check_move_field = vals.get('check_move_field')
            signal = vals.get('signal')

            move = self.env['account.move'].with_context({}).create(move_vals)
            debit_line_vals['move_id'] = move.id
            credit_line_vals['move_id'] = move.id
            _logger.info(f"debit_line_vals despues de get_vals: {debit_line_vals}")
            _logger.info(f"credit_line_vals despues de get_vals: {credit_line_vals}")

            move.line_ids.with_context(check_move_validity=False).create(debit_line_vals)
            move.line_ids.with_context(check_move_validity=False).create(credit_line_vals)

            # check.write({check_move_field: move.id})
            # check.action_deposit();
            _logger.info(f"move para utilidad: {move}")
            move.action_post()
            self.move_id = move

    def get_vals(self, suma, date, diario, monto_pago, moneda):

        # vou_journal = check.voucher_id.journal_id

        # if self.action_type == 'deposit':
        #ref = 'Orden de Pago. ' + self.name
        ref = 'Utilidad cambio OP ' + self.name
        # check_move_field = 'deposit_account_move_id'
        journal = self.env['account.journal'].search(
            [('type', '=', 'general'), ('company_id', '=', self.env.company.id)], limit=1)

        debit_account_id = self.partner_id.property_account_payable_id.id

        credit_account_id = self.env.company.income_currency_exchange_account_id.id
        signal = 'Excedente Recibo Nro.' + self.name
        monto_mon_ex_c = None
        monto_mon_ex_d = None
        # seq_id = self.env['ir.sequence'].search([('id', '=', journal.sequence_id.id)])
        if moneda.id != self.env.company.currency_id.id:
            monto_mon_ex = monto_pago
            moneda = moneda.id
        else:
            monto_mon_ex = None
            moneda = moneda.id
        # name = seq_id._next()
        name = 'Diferencia OP Nro.' + self.name

        # ref += check.name
        move_vals = {
            'name': name,
            'journal_id': journal.id,
            'date': date,
            'ref': ref,
        }

        if not monto_mon_ex:
            monto_mon_ex = 0
        debit_line_vals = {
            'name': ref,
            'account_id': debit_account_id,
            'partner_id': self.partner_id.id,
            'debit': suma,
            'currency_id': moneda,
            # 'amount_currency': monto_mon_ex,
            'credit': 0,
            'ref': ref,
        }

        # raise exceptions.ValidationError(debit_line_vals['ref'])
        credit_line_vals = {
            'name': ref,
            'account_id': credit_account_id,
            'partner_id': self.partner_id.id,
            'currency_id': moneda,
            # 'amount_currency': - monto_mon_ex,
            'debit': 0,
            'credit': suma,
            'ref': ref,
        }
        _logger.info(f"move vals: {move_vals}")
        _logger.info(f"credit_line_vals: {credit_line_vals}")
        _logger.info(f"debit_line_vals: {debit_line_vals}")
        # raise exceptions.ValidationError(credit_line_vals['amount_currency'])
        return {
            'move_vals': move_vals,
            'debit_line_vals': debit_line_vals,
            'credit_line_vals': credit_line_vals,

            'signal': signal,
        }

    def _crear_diferencia_cambio(self):
        for recibo in self:
            if recibo.diferencia_cambio != 0 and abs(recibo.diferencia_cambio) > 1:
                self.asiento_diferencia(recibo.diferencia_cambio, recibo.diario_diferencia, recibo.currency_id)

    def asiento_diferencia(self, pago, diario, moneda):
        rate_recibo = \
        self.env['res.currency.rate'].search([('currency_id', '=', moneda.id), ('name', '=', self.fecha)])[0].set_venta
        # cuenta_a_cobrar = self.env.ref('account.data_account_type_receivable').id
        # debit_lines_reconcile = self.env['account.move.line'].search([('invoice_id','=',invoice_id.id),('account_id.user_type_id','=',cuenta_a_cobrar),('debit','>',0),('move_id.state','=','posted')])
        # if not len(debit_lines_reconcile) > 0:
        #     raise ValidationError('Favor revisar que la cuenta contable de obligacion de la factura se encuentre configurada como a cobrar')
        # monto_gs_inicial = rate_recibo * monto_ext
        # diferencia_cambio_inicial = (debit_lines_reconcile[0].debit - monto_gs_inicial)  + pago
        fecha = self.fecha
        vals = self.get_vals_cambio(pago, fecha, diario)
        move_vals = vals.get('move_vals', {})
        debit_line_vals = vals.get('debit_line_vals', {})
        credit_line_vals = vals.get('credit_line_vals', {})
        move = self.env['account.move'].with_context(check_move_validity=False).create(move_vals)
        for deb in debit_line_vals:
            deb['move_id'] = move.id
            move.line_ids.with_context(check_move_validity=False).create(deb)
        for cred in credit_line_vals:
            # debit_line_vals['move_id'] = move.id
            cred['move_id'] = move.id
            move.line_ids.with_context(check_move_validity=False).create(cred)
        lines_to_reconcile = list()
        # check.write({check_move_field: move.id})
        # check.action_deposit();
        move.action_post()

        # credit_lines_reconcile = self.env['account.move.line'].search([('invoice_id','=',invoice_id.id),('account_id.user_type_id','=',cuenta_a_cobrar),('credit','>',0),('move_id.state','=','posted')])

        # for d in debit_lines_reconcile:
        #     lines_to_reconcile.append(d.id)
        # for c in credit_lines_reconcile:
        #     lines_to_reconcile.append(d.id)
        self.move_diferencia_id = move

        # partial_reconcile_id = self.env['account.partial.reconcile'].create(
        #     {
        #         'debit_move_id': debit_lines_reconcile[0].id,
        #         'credit_move_id': move.line_ids.filtered(lambda x : x.account_id.user_type_id.id == cuenta_a_cobrar).id,
        #         'amount': diferencia_cambio_inicial + pago,
        #         'max_date': self.fecha
        #     }
        # )
        # full_reconcile_id = self.env['account.full.reconcile'].create({
        #     'exchange_move_id':move.id,
        #     'reconciled_line_ids': [(6, 0, lines_to_reconcile)],
        # })
        # for d in debit_lines_reconcile:
        #     d.full_reconcile_id = full_reconcile_id.id
        # for c in credit_lines_reconcile:
        #     c.full_reconcile_id = full_reconcile_id.id
        # partial_reconcile_id.full_reconcile_id = full_reconcile_id.id

    def get_vals_cambio(self, suma, date, diario):
        vals_cred = list()
        vals_debit = list()
        val_c = 0
        val_d = 0
        ref = 'Diferencia de tasa de cambio OP ' + self.name
        # cuenta_ganancia = self.env['res.config.settings'].sudo().search([], limit=1,
        #                                                                 order="id desc").income_currency_exchange_account_id
        # cuenta_perdida = self.env['res.config.settings'].sudo().search([], limit=1,
        #                                                                order="id desc").expense_currency_exchange_account_id

        cuenta_ganancia = self.env.company.income_currency_exchange_account_id
        cuenta_perdida = self.env.company.expense_currency_exchange_account_id
        if not cuenta_ganancia or not cuenta_perdida:
            raise ValidationError(
                'Favor especificar cuenta de ganancia y pérdida por tasa cambiaria en ajustes de la compañía')
        journal = diario
        if suma < 0:
            credit_account_id = self.cuenta_diferencia.id
            debit_account_id = self.cuenta_diferencia.id
            val_d = 1
        else:
            credit_account_id = self.cuenta_diferencia.id
            # debit_account_id = self.partner_id.property_account_payable_id.id
            debit_account_id = self.cuenta_diferencia.id
            val_c = 1

        # ref += check.name
        move_vals = {
            'journal_id': journal.id,
            'date': date,
            'ref': ref,
        }

        rate = self.env['res.currency.rate'].search(
            [('currency_id', '=', self.currency_id.id), ('name', '=', self.fecha)])
        # if len(rate) > 0:
        #     suma += f.monto_gs - (f.monto * rate.set_venta)
        agg = 0
        pay = self.payment_ids.filtered(lambda r: r.journal_id.type in ('bank', 'cash'))
        for payments in pay:
            if payments.monto_moneda_pago > 0:
                acor = round((payments.monto_moneda_pago - (rate.set_venta * payments.amount)), 2)
                # agg+=abs(abs(round(acor,2)))
                if acor < 0:
                    agg += abs(abs(round(acor, 2)))
                    vls = {
                        'name': ref,
                        'account_id': payments.journal_id.default_account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': abs(round(acor, 2)),
                        'reconciled': True,
                        'credit': 0,
                        'ref': ref,
                    }
                    vals_debit.append(vls)
                else:
                    agg -= abs(abs(round(acor, 2)))
                    vls = {
                        'name': ref,
                        'account_id': payments.journal_id.default_account_id.id,
                        'partner_id': self.partner_id.id,
                        'debit': 0,
                        'credit': abs(round(acor, 2)),
                        'ref': ref,
                    }
                    vals_cred.append(vls)
        # acor = abs(self.diferencia_cambio)
        if agg != 0:
            acor = abs(agg)
        else:
            acor = abs(self.diferencia_cambio)
        if suma > 0:

            debit_line_vals = {
                'name': ref,
                'account_id': cuenta_ganancia.id,
                'partner_id': self.partner_id.id,
                'debit': abs(round(acor, 2)),
                'credit': 0,
                'ref': ref,
            }
            vals_debit.append(debit_line_vals)
        else:

            credit_line_vals = {
                'name': ref,
                'account_id': cuenta_perdida.id,
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'debit': 0,
                'credit': abs(round(acor, 2)),
                'ref': ref,
            }
            vals_cred.append(credit_line_vals)
        self.verificar_descuadre(vals_debit, vals_cred)

        return {
            'move_vals': move_vals,
            'debit_line_vals': vals_debit,
            # 'credit_line_vals': credit_line_vals,
            'credit_line_vals': vals_cred,
        }

    def verificar_descuadre(self, vals_debit, vals_cred):
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

    def verificar_crear_cheques(self):
        cheques = list()
        for rec in self:
            for p in rec.payment_ids:
                if p.numero_cheque_pago:
                    vals = {
                        'number': p.numero_cheque_pago,
                        'amount': p.amount,
                        'checkbook_id': p.checkbook_id.id,
                        'voucher_id': p.id,
                        'state': 'draft'
                    }
                self.env['account.check'].create(vals)

    def set_borrador(self):
        for record in self:
            _logger.warning('ACA SE LLAMA')
            if record.state != 'confirmado':
                record.state = 'borrador'
                continue
            # raise ValidationError('HOLA SI BUENAS TARDES')
            for p in record.payment_ids:
                p.with_context(skip_account_move_synchronization=True).action_draft()
                if not p.asignar_factura:
                    p.reconciled_invoice_ids = [(5, 0, 0)]
                # for f in p.fac_ids:
                # p.fac_ids.unlink()
            _logger.warning("WWWWWWWWWWWWWWWWW")
            if record.payment_ids:
                for pay in record.payment_ids:
                    moves = record.env['account.move.line'].search([('payment_id', '=', pay.id)])
                    if len(moves) > 0:
                        for m in moves:
                            if m.full_reconcile_id:
                                m.full_reconcile_id.partial_reconcile_ids.unlink()
                            m.remove_move_reconcile()

            if record.check_ids:
                for cheques in record.check_ids:
                    if cheques.state != 'draft':
                        raise ValidationError(
                            'No se puede eliminar un cheque que no este en estado Emitido')
                    else:
                        cheques.unlink()

            if record.move_id:
                for move in record.move_id:
                    for lineas in move.line_ids:
                        lineas.remove_move_reconcile()
                    move.button_cancel()
                    move.unlink()
            if record.move_diferencia_id:
                for move in record.move_diferencia_id:
                    for lineas in move.line_ids:
                        lineas.remove_move_reconcile()
                    move.button_cancel()
                    move.unlink()
            _logger.warning('AAAAAAAAAAAAAA')
            for fac in record.orden_pagos_facturas_ids:
                movelines = fac.invoice_id.line_ids
                _logger.warning('MOVELINES %s', movelines)
                for line in movelines:
                    if line.reconciled:
                        line.remove_move_reconcile()
                fac.amount = 0

            # detalle_caja=record.env['ruc.caja.detalle'].search([('orden_pago_id.id','=',record.id)])
            # if detalle_caja.caja_id.state == 'abierto':
            #     detalle_caja.unlink()
            # else:
            #     raise ValidationError('La caja ya NO se encuentra Abierta, NO puede pasar a borrador el recibo')
            record.state = 'borrador'

    @api.onchange('partner_id')
    def limpiar_lineas_facturas(self):
        if self.orden_pagos_facturas_ids:
            raise ValidationError('Elimine las facturas que se agrego del cliente anterior')
        if self.payment_ids:
            raise ValidationError('Elimine los cobros que se agrego del cliente anterior')

    @api.onchange('orden_pagos_facturas_ids', 'partner_id')
    def ver_facturas(self):
        if self.partner_id:
            lista_factura = []
            lista_facturas_abiertas = []
            lista_a_mostrar = []
            # fac_abiertas = self.env['account.move'].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'open')])
            fac_abiertas = self.env['account.move'].search(
                [('partner_id', 'child_of', self.partner_id.id), '|', ('state', '=', 'open'),
                 ('move_type', '=', 'in_invoice')])
            for rec in self.orden_pagos_facturas_ids:
                if rec.invoice_id:
                    lista_factura.append(rec.invoice_id)
            for f in fac_abiertas:
                if f.no_ver_factura_pago:
                    fac = self.env['account.move'].search([('id', '=', f.id)])
                    dato = {
                        'no_ver_factura_pago': False
                    }
                    fac.write(dato)
                lista_facturas_abiertas.append(f)

            lista_factura = set(lista_factura)
            lista_facturas_abiertas = set(lista_facturas_abiertas)
            lista_a_mostrar = lista_factura & lista_facturas_abiertas
            for f in lista_a_mostrar:
                fac = self.env['account.move'].search([('id', '=', f.id)])
                dato = {
                    'no_ver_factura_pago': True
                }
                fac.write(dato)

    def limpiar_facturas(self):

        if self.partner_id:
            lista_factura = []
            lista_facturas_abiertas = []
            lista_a_mostrar = []
            fac_abiertas = self.env['account.move'].search(
                [('partner_id', '=', self.partner_id.id), ('state', '=', 'open')])
            for rec in self.orden_pagos_facturas_ids:
                if rec.invoice_id:
                    lista_factura.append(rec.invoice_id)
            for f in fac_abiertas:
                if f.no_ver_factura_pago:
                    fac = self.env['account.move'].search([('id', '=', f.id)])
                    dato = {
                        'no_ver_factura_pago': False
                    }
                    fac.write(dato)
                lista_facturas_abiertas.append(f)

            lista_factura = set(lista_factura)
            lista_facturas_abiertas = set(lista_facturas_abiertas)
            lista_a_mostrar = lista_factura & lista_facturas_abiertas
            for f in lista_a_mostrar:
                fac = self.env['account.move'].search([('id', '=', f.id)])
                dato = {
                    'no_ver_factura_pago': True
                }
                fac.write(dato)

    def get_numero_actual(self):
        for rec in self:
            if not rec.name:
                op = self.env["account.orden.pago"].sorted(key=lambda r: r.secuencia, reverse=True, limit=1)
                rec.secuencia = op.secuencia + 1
                rec.name = 'OP/' + str(rec.secuencia)

    def unlink(self):

        if self.state != 'borrador':
            raise ValidationError("Solo se puede elmininar un recibo en estado  Borrador")
        if self.orden_pagos_facturas_ids:
            raise ValidationError(
                "Para poder eliminar la orden de pago favor elimine sus lineas de Factura primeramente.")
        if self.payment_ids:
            raise ValidationError(
                "Para poder eliminar la orden de pago favor elimine sus lineas de Pagos primeramente.")
        return super(models.Model, self).unlink()

    def agregar_punto_de_miles(self, numero, moneda):
        _logger.info("##################agregar punto de miles##################")
        _logger.info(numero)
        _logger.info(moneda)
        entero = int(numero)
        if 'USD' in moneda:
            decimal = str(numero)
            numero_con_punto = ''
            print(f"decimal ->{decimal}")
            entero_string = '.'.join([str(int(entero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                            ::-1]
            print(f"entero_string->{entero_string}")
            decimal_string = str(decimal).split('.')
            print(f"decimal_string->{decimal_string}")
            _logger.info("###########decimal_string##########")
            _logger.info(decimal_string)
            if decimal_string and len(decimal_string) > 1:
                if decimal_string and len(decimal_string[1]) >= 2:
                    numero_con_punto = entero_string + ',' + decimal_string[1][:2]
                elif len(decimal_string[1]) < 2 and decimal_string[1] != '0':
                    numero_con_punto = entero_string + ',' + decimal_string[1] + '0'
                elif len(decimal_string[1]) < 2 and decimal_string[1] == '0':
                    numero_con_punto = entero_string + ',' + decimal_string[1] + '0'
            else:
                numero_con_punto = entero_string
        else:
            numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                               ::-1]
        num_return = numero_con_punto
        return num_return

    def redondeo_por_tres_decimales_fact(self, numero, moneda):
        print(type(numero))
        _logger.info("#####################REDONDEO#######################")
        _logger.info(numero)
        ajuste = 5
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
                if decimal3 >= ajuste and (decimal2 + 1) > 9 and (decimal1 + 1) > 9:
                    numero += 1
                    flotante = float(numero)
                    return flotante
                elif decimal3 >= ajuste and (decimal2 + 1) >= ajuste and (decimal2 + 1) < 10:
                    decimal2 += 1
                    letter_decimal = str(decimal1) + str(decimal2)
                    flotante = float(str(numero) + '.' + letter_decimal)
                    print(f"flotante ->{flotante}")
                    return flotante
                elif decimal3 >= ajuste and (decimal2 + 1) >= ajuste and (decimal1 + 1) < 10:
                    decimal1 += 1
                    letter_decimal = str(decimal1)
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

    def pasaaentero_(self, a):
        return int(a)

    def cambiapuntoporcoma(self, a):
        b = str(a)
        c = b.replace(".", ",")
        return c

    def sacasimbolo_(self, a):
        b = str(a)
        c = b.split(" ")

        return c[0]

    def agregar_punto_de_miles_(self, numero):
        numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(numero))), 3)])[::-1]
        return numero_con_punto

    def puntodemiles(self, a):
        b = str(a)
        c = b.split(',')
        if len(c) > 1:
            d = self.agregar_punto_de_miles_(c[0])
            e = str(d) + ',' + str(c[1])
            return e
        else:
            return b

    @api.depends('payment_ids.journal_id')
    def _compute_mostrar_datos_bancarios(self):
        for rec in self:
            rec.mostrar_datos_bancarios = any(
                pago.journal_id.tipo_pago == '5'
                for pago in rec.payment_ids
                if hasattr(pago.journal_id, 'tipo_pago')
            )


class PagosFactura(models.Model):
    _name = 'account.orden.pago.factura'

    name = fields.Char(string="", readonly=True)
    invoice_id = fields.Many2one('account.move', 'Factura')
    move_line_id = fields.Many2one('account.move.line', 'Apunte')
    amount = fields.Float(string="Monto Nota Credito")
    orden_pago_id = fields.Many2one('account.orden.pago')
    partner_id = fields.Many2one('res.partner', related='orden_pago_id.partner_id')
    fecha_pago = fields.Date(related='orden_pago_id.fecha')
    currency_id = fields.Many2one('res.currency', related='orden_pago_id.currency_id')
    currency_invoice = fields.Many2one('res.currency', compute='get_move_data')
    date_invoice = fields.Date(compute='get_move_data')
    nro_factura = fields.Char()
    amount_total = fields.Monetary(readonly=True, compute='_set_pago', currency_field="currency_invoice")
    residual = fields.Monetary(compute='_set_pago', currency_field="currency_invoice")
    monto = fields.Float(string="Pago")
    monto_gs = fields.Float(string="Pago Gs.")
    viene_del_pago = fields.Boolean(default=False)
    paso_por_el_pago = fields.Integer(default=0)
    moneda_company = fields.Boolean(compute="_get_orden_pago_currency")
    account_payable = fields.Many2one('account.account', string="Cuenta a Pagar", compute="get_payable_account")

    @api.onchange('invoice_id', 'move_line_id')
    def check_payable_account(self):
        for rec in self:
            cuenta = None
            if rec.invoice_id:
                cuenta = rec.orden_pago_id.orden_pagos_facturas_ids.mapped('invoice_id').mapped('line_ids').mapped(
                    'account_id').filtered(lambda r: r.account_type == 'liability_payable')
                # cuentas = rec.orden_pagos_facturas_ids.mapped('invoice_id').mapped('line_ids').mapped(
                #     'account_id').filtered(lambda r: r.internal_type == 'payable')
                if len(cuenta) > 1:
                    raise ValidationError(
                        'No puede pagar en una misma orden de pago facturas con diferentes cuentas a Pagar')
            elif rec.move_line_id:
                cuenta = rec.orden_pago_id.orden_pagos_facturas_ids.mapped('move_line_id').mapped('account_id')
                # cuentas = rec.orden_pagos_facturas_ids.mapped('invoice_id').mapped('line_ids').mapped(
                #     'account_id').filtered(lambda r: r.internal_type == 'payable')
                if len(cuenta) > 1:
                    raise ValidationError(
                        'No puede pagar en una misma orden de pago deudas con diferentes cuentas a Pagar')

    @api.depends('invoice_id', 'move_line_id')
    def get_payable_account(self):
        for rec in self:
            cuenta = None
            if rec.invoice_id:
                cuenta = rec.invoice_id.mapped('line_ids').mapped('account_id').filtered(
                    lambda r: r.account_type == 'liability_payable')
                if cuenta:
                    cuenta = cuenta[0]
            elif rec.move_line_id:
                cuenta = rec.move_line_id.account_id
            rec.account_payable = cuenta

    @api.depends('invoice_id', 'move_line_id')
    def get_move_data(self):
        for rec in self:
            rec.date_invoice = False
            rec.currency_invoice = False
            if rec.invoice_id:
                rec.date_invoice = rec.invoice_id.invoice_date
                rec.currency_invoice = rec.invoice_id.currency_id
            elif rec.move_line_id:
                rec.date_invoice = rec.move_line_id.date_maturity
                rec.currency_invoice = rec.move_line_id.currency_id

    @api.depends('currency_id')
    def _get_orden_pago_currency(self):
        for rec in self:
            if rec.orden_pago_id:
                if rec.orden_pago_id.currency_id != self.env.company.currency_id:
                    rec.moneda_company = False
                else:
                    rec.moneda_company = True

    @api.depends('invoice_id', 'move_line_id')
    def _set_pago(self):
        # for r in self:
        #     if not r.orden_pago_id.currency_id:
        #         raise ValidationError('Debe seleccionar la moneda de la Orden de pago')
        for rec in self.sorted(key=lambda r: r.amount, reverse=True):

            if rec.invoice_id:
                if rec.invoice_id.move_type in ('out_refund', 'in_refund'):
                    if rec.monto == 0:
                        if rec.invoice_id.amount_residual_signed == 0:
                            rec.monto = rec.invoice_id.amount_total_signed
                        else:
                            rec.monto = rec.invoice_id.amount_residual_signed

                    if rec.amount == rec.invoice_id.amount_residual_signed or rec.amount == 0:
                        rec.amount = rec.invoice_id.amount_residual_signed
                    if rec.monto != rec.invoice_id.amount_residual_signed and rec.monto != 0:
                        rec.amount = rec.monto
                    rec.amount_total = rec.invoice_id.amount_total_signed
                    rec.residual = rec.invoice_id.amount_residual_signed
                else:
                    if not rec.viene_del_pago:
                        residual_currency = rec.invoice_id.amount_residual
                        if rec.currency_id != rec.invoice_id.currency_id:
                            residual_currency = rec.invoice_id.currency_id._convert(
                                rec.invoice_id.amount_residual, rec.currency_id, date=rec.fecha_pago)
                        if rec.monto == 0:
                            rec.monto = residual_currency
                        if rec.amount == residual_currency or rec.amount == 0:
                            rec.amount = residual_currency
                        if rec.monto != residual_currency and rec.monto != 0:
                            rec.amount = rec.monto
                        # rec.residual = rec.invoice_id.amount_residual
                        rec.amount_total = rec.invoice_id.amount_total
                        rec.residual = rec.invoice_id.amount_residual
            elif rec.move_line_id:
                if not rec.viene_del_pago:
                    if rec.move_line_id.amount_currency != 0:
                        residual_currency = abs(rec.move_line_id.amount_residual_currency)
                    else:
                        residual_currency = abs(rec.move_line_id.balance)
                    if rec.currency_id != rec.move_line_id.currency_id:
                        residual_currencfy = rec.move_line_id.currency_id._convert(
                            abs(rec.move_line_id.balance), rec.currency_id, date=rec.fecha_pago)
                    if rec.monto == 0:
                        rec.monto = residual_currency
                    if rec.amount == residual_currency or rec.amount == 0:
                        rec.amount = residual_currency
                    if rec.monto != residual_currency and rec.monto != 0:
                        rec.amount = rec.monto
                    rec.residual = abs(residual_currency)
                    if rec.move_line_id.amount_currency != 0:
                        rec.amount_total = abs(rec.move_line_id.amount_currency)
                    else:
                        rec.amount_total = abs(rec.move_line_id.balance)

            else:
                rec.amount_total = 0
                rec.residual = 0
                rec.amount = 0
                rec.monto = 0

    def verificar_amount(self):
        if self.invoice_id.move_type in ('out_refund', 'in_refund'):
            pass
        else:
            self.amount = self.monto
