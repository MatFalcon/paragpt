# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
import datetime
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    orden_pago_id = fields.Many2one('account.orden.pago')
    monto_cheque_pago = fields.Float()
    banco_cheque_pago = fields.Many2one('res.bank')
    banco_cuenta_pago = fields.Many2one('res.partner.bank')
    numero_cheque_pago = fields.Integer(string="Nro. de cheque")
    nro_recibo_pago = fields.Char(string="Recibo", compute="_verificar_recibo")
    fecha_cheque_pago = fields.Date()
    fecha_cheque_diferido = fields.Date()
    cheque_propio = fields.Boolean(compute="es_cheque_propio", default=False)
    titular_pago = fields.Char()
    nro_cuenta_pago = fields.Char()
    tipo_de_cheque_pago = fields.Selection([('diferido', 'Diferido'), ('vista', 'A la vista')])
    ver_cuenta_banco_pago = fields.Boolean()
    observaciones = fields.Char()
    monto_moneda_pago = fields.Monetary(currency_field='moneda_pago', string="Monto Moneda")
    moneda_pago = fields.Many2one('res.currency')
    ver_otra_moneda = fields.Boolean(compute="verificar_monedas")
    cotizacion = fields.Float()
    asignar_factura = fields.Boolean("Asignar facturas", default=False)
    reconciled_invoice_ids_op = fields.Many2many(related='orden_pago_id.reconciled_invoice_ids')
    extranjero = fields.Boolean(compute='verificar_monedas')
    balance_foreign_account = fields.Float(compute='compute_balance')
    balance = fields.Float(compute='compute_balance')
    tipo_op = fields.Selection(related='orden_pago_id.tipo', store=True, string="Tipo de orden de pago")
    monto_pago = fields.Float(string="Importe")
    correo_enviado = fields.Boolean(string="Correo Enviado", default=False, copy=False, tracking=True)
    journal_id_tmp = fields.Many2one('account.journal', string='Diario')
    fecha_factura = fields.Date( string="Fecha de Factura", store=True)
    numero_factura = fields.Char(string="Número de Factura", readonly=True, copy=False, store=True)


    @api.depends('journal_id')
    def _compute_currency_id(self):
        for pay in self:
            pay.currency_id = pay.orden_pago_id.currency_id or pay.journal_id.currency_id or pay.journal_id.company_id.currency_id

    def actualizar_monto_moneda(self):
        if self.state == 'posted':
            if self.payment_type == "outbound":
                for line in self.move_id.line_ids:
                    if line.credit != 0:

                        sql_query_move_line = """
                                           UPDATE account_move_line
                                           SET amount_currency = %s,
                                           currency_id = %s
                                           WHERE id = %s;
                                       """
                        params_payment = (-(self.monto_moneda_pago), self.moneda_pago.id, line.id)
                        self.env.cr.execute(sql_query_move_line, params_payment)
                    else:
                        sql_query_move_line = """
                                                                   UPDATE account_move_line
                                                                   SET amount_currency = %s,
                                                                   currency_id = %s
                                                                   WHERE id = %s;
                                                               """
                        params_payment = (self.monto_moneda_pago, self.moneda_pago.id, line.id)
                        self.env.cr.execute(sql_query_move_line, params_payment)


    # @api.onchange('journal_id_tmp', 'journal_id')
    # def set_journal_id_tmp_op(self):
    #     for rec in self:
    #         if rec.journal_id_tmp:
    #             rec.journal_id = rec.journal_id_tmp
    #         if rec.journal_id:
    #             rec.journal_id_tmp = rec.journal_id

    @api.model
    def enviarRecibosDia(self):
        recibos = self.env['account.payment'].search([('state', '=', 'posted'),
                                                      ('payment_type', '=', 'inbound'),
                                                      ('correo_enviado', '=', False),
                                                      ('date', '<=', datetime.date.today()),
                                                      ('date', '>', '2024-01-15')])
        for r in recibos.filtered(lambda x: x.is_matched):
            template = self.env.ref('account.mail_template_data_payment_receipt')
            destinatarios = [r.partner_id.id]
            copias = self.env.user.company_id.partner_id.email + ', '
            if r.partner_id.child_ids:
                for c in r.partner_id.child_ids.filtered(lambda x: x.email):
                    copias += c.email + ', '
            if destinatarios:
                vals = {
                    'recipient_ids': destinatarios,
                    'email_from': self.env.user.company_id.email,
                    'author_id': self.env.user.id,
                    'email_cc': copias,
                }
                template.send_mail(r.id, email_values=vals, force_send=True)
                r.write({'correo_enviado': True})

    @api.model
    def create(self, vals):
        if self._context.get('dont_redirect_to_payments'):
            return super(AccountPayment, self).create(vals)
        return super(AccountPayment, self).create(vals)

    def write(self, vals):
        if self._context.get('dont_redirect_to_payments'):
            return super(AccountPayment, self).create(vals)
        return super(AccountPayment, self).write(vals)

    @api.depends('fecha_cheque_pago')
    def cambiar_diferido(self):
        for rec in self:
            if rec.fecha_cheque_pago:
                rec.fecha_cheque_diferido = rec.fecha_cheque_pago

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer')
    def _compute_destination_account_id(self):
        cuenta = self._context.get('cuenta')
        if cuenta:
            self.destination_account_id = cuenta
        else:
            super(AccountPayment, self)._compute_destination_account_id()

    @api.depends('numero_cheque_pago')
    def _verificar_recibo(self):
        for rec in self:
            cheques = self.env['account.check'].search([('number', '=', rec.numero_cheque_pago)])
            if cheques:
                # Usamos una comprensión de lista para recoger todos los nro_recibo_pago de los cheques
                rec.nro_recibo_pago = ', '.join(cheque.recibo for cheque in cheques if cheque.recibo)
            else:
                rec.nro_recibo_pago = False

    @api.depends('journal_id')
    def compute_balance(self):
        for rec in self:
            m = 0
            if rec.journal_id:
                if rec.journal_id.currency_id and rec.journal_id.currency_id != self.env.company.currency_id:
                    saldos = self.env['account.move.line'].search([('move_id.state', '=', 'posted'), (
                        'account_id', '=', rec.journal_id.default_account_id.id)])
                    m = sum([m.amount_currency for m in saldos])
                else:
                    saldos = self.env['account.move.line'].search([('move_id.state', '=', 'posted'), (
                        'account_id', '=', rec.journal_id.default_account_id.id)])
                    m = sum([m.balance for m in saldos])
            rec.balance = m
            rec.balance_foreign_account = m

    @api.depends('moneda_pago')
    def verificar_monedas(self):
        for rec in self:
            if rec.moneda_pago:
                if self.env.company.currency_id != rec.moneda_pago:
                    rec.ver_otra_moneda = True
                else:
                    rec.ver_otra_moneda = False
            else:
                rec.ver_otra_moneda = False
            if self.journal_id.currency_id:
                if self.env.company.currency_id != self.journal_id.currency_id:
                    rec.extranjero = True
                else:
                    rec.extranjero = False
            else:
                rec.extranjero = False

    @api.depends('moneda_pago', 'journal_id')
    def obtener_moneda_op(self):
        if self.orden_pago_id:
            moneda = self._context.get('default_moneda_pago')
            if moneda:
                if self.moneda_pago:
                    moneda_op = self.env['res.currency'].browse(moneda)
                    # self.currency_id = moneda_op

    @api.onchange('checkbook_id')
    def obtener_cheque(self):
        for rec in self:
            if rec.checkbook_id:
                if rec.checkbook_id.journal_id != rec.journal_id:
                    raise ValidationError(_("La chequera seleccionada no pertenece al diario seleccionado."))
                rec.numero_cheque_pago = rec.checkbook_id.next_check_number
            else:
                rec.numero_cheque_pago = False

    @api.depends('banco_cheque_pago')
    def _verficar_cuenta_banco(self):
        for rec in self:
            cuenta = self.env['res.partner.bank'].search(
                [('partner_id', '=', rec.partner_id.id), ('bank_id', '=', rec.banco_cheque.id)])
            if cuenta:
                rec.ver_cuenta_banco_pago = True
            else:
                rec.ver_cuenta_banco_pago = False
                rec.titular_pago = None
                rec.nro_cuenta_pago = None

    @api.constrains('amount')
    def verificar_monto_cero(self):
        for rec in self:
            if rec.orden_pago_id:
                if rec.amount == 0:
                    if rec.monto_cheque_pago > 0:
                        rec.amount = rec.monto_cheque_pago
                    else:
                        continue
                        raise ValidationError('El cobro no  puede guardar con monto 0')

    @api.depends('monto_cheque_pago')
    def _set_monto_del_pago(self):
        for rec in self:
            if rec.monto_cheque_pago > 0:
                rec.amount = rec.monto_cheque_pago
                rec.checks_amount = rec.monto_cheque_pago

    @api.depends('banco_cuenta_pago')
    def _datos_cheque(self):
        for rec in self:
            cuenta = self.env['res.partner.bank'].search([('id', '=', rec.banco_cuenta.id)])
            if cuenta:
                rec.nro_cuenta = cuenta.acc_number
                rec.titular = cuenta.titular
            else:
                rec.nro_cuenta = None
                rec.titular = None

    @api.depends('journal_id')
    def es_cheque_propio(self):
        for rec in self:
            if rec.journal_id.payment_subtype == 'issue_check':
                rec.cheque_propio = True
            else:
                rec.cheque_propio = False
                rec.nro_cuenta_pago = None
                rec.titular_pago = None
                rec.banco_cheque_pago = None
                rec.banco_cuenta_pago = None
                rec.fecha_cheque_pago = None
                rec.numero_cheque_pago = None

    @api.depends('received_third_check_ids')
    def _calcular_cheque(self):
        for rec in self:
            for c in rec.received_third_check_ids:
                rec.monto_cheque = c.amount
                rec.banco_cheque = c.bank_id.name
                rec.numero_cheque = c.number
                if c.date:
                    rec.fecha_cheque = c.date
                else:
                    rec.fecha_cheque = c.issue_date

    def agregar_punto_de_miles(self, numero):
        entero = int(numero)
        decimal = '{0:.3f}'.format(numero - entero)
        entero_string = '.'.join([str(int(entero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[::-1]
        if decimal == '0.000':
            numero_con_punto = entero_string
        else:
            decimal_string = str(decimal).split('.')
            numero_con_punto = entero_string + ',' + decimal_string[1]
        return numero_con_punto



