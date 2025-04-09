# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError




class AccountPayment(models.Model):
    _inherit = 'account.payment'

    invoice_ids = fields.Many2many('account.move', string="Facturas del pago",
                     help="Invoices whose journal items have been reconciled with these payments.")
    recibo_id = fields.Many2one('account.recibo')
    monto_cheque_recibo = fields.Float()
    es_transferencia=fields.Boolean(default=False,string="Es transferencia")
    banco_cheque_recibo = fields.Many2one('res.bank')
    banco_cuenta_recibo = fields.Many2one('res.partner.bank')
    numero_cheque_recibo = fields.Char()
    fecha_cheque_recibo = fields.Date()
    fecha_cheque_diferido = fields.Date(string="Fecha de Cobro Cheque",help="En caso de que el cheque sea diferido este campo debe ser distinto a fecha cheque recibo")
    cheque_tercero=fields.Boolean(compute="es_cheque_tercero",store=True)
    titular_recibo=fields.Char()
    nro_cuenta_recibo=fields.Char(string="Nro. de Cuenta")
    tipo_de_cheque_recibo=fields.Selection([('diferido','Diferido'),('vista','A la vista')])
    numero_transaccion = fields.Char(string="Nro de Cheque/Retencion/Transaccion")
    ver_cuenta_banco_recibo=fields.Boolean()
    tipo_diario = fields.Selection(related='journal_id.type',string="Tipo diario")
    cobrar_dif_moneda=fields.Boolean()
    cotizacion=fields.Float()
    monto_alternativo_2=fields.Float()
    ver_monto_alternativo_2=fields.Boolean()
    recibo_invoice_ids = fields.Many2many(related='recibo_id.recibo_invoice_ids',string="Facturas del recibo")
    recibo_apunte_ids = fields.Many2many(related='recibo_id.recibo_apunte_ids',string="Apuntes del recibo")
    tipo_recibo = fields.Selection(related='recibo_id.tipo',store=True,string="Tipo de recibo")
    currency_id_tmp = fields.Many2one('res.currency',string="Divisa")

    # @api.onchange('journal_id_tmp','journal_id')
    # def set_journal_id_tmp_recibo(self):
    #     for rec in self:
    #         if rec.journal_id_tmp:
    #             rec.journal_id = rec.journal_id_tmp
    #         if rec.journal_id:
    #             rec.journal_id_tmp = rec.journal_id

    @api.onchange('fecha_cheque_recibo')
    def cambiar_diferido(self):
        for rec in self:
            rec.fecha_cheque_diferido=rec.fecha_cheque_recibo

    @api.onchange('partner_id')
    def _change_communication(self):
        self.ensure_one()
        if self.recibo_id:
            if self.recibo_id.obs:
                self.ref = self.recibo_id.obs

    @api.onchange('cotizacion','monto_cheque_recibo','monto_moneda_pago')
    def calculo_cotizacion(self):
        if self.recibo_id:
            self.currency_id = self.recibo_id.currency_id
            if self.recibo_id.cobrar_dif_moneda:
                if self.cheque_tercero:
                    if self.cotizacion > 0 and self.monto_cheque_recibo > 0:
                        if self.moneda_pago != self.env.company.currency_id:
                            self.amount = round(self.monto_moneda_pago * self.cotizacion, 2)
                        else:
                            self.amount = round(self.monto_moneda_pago / self.cotizacion, 2)
                else:
                    if self.monto_moneda_pago > 0  and self.cotizacion > 0:
                        if self.moneda_pago != self.env.company.currency_id:
                            self.amount = round(self.monto_moneda_pago * self.cotizacion, 2)
                        else:
                            self.amount = round(self.monto_moneda_pago / self.cotizacion, 2)
        if self.orden_pago_id:
            if self.monto_moneda_pago > 0  and self.cotizacion > 0:
                if self.moneda_pago != self.env.company.currency_id:
                    self.amount = round(self.monto_moneda_pago * self.cotizacion, 2)
                else:
                    self.amount = round(self.monto_moneda_pago / self.cotizacion, 2)
    # @api.constrains('numero_transaccion')
    @api.onchange('numero_transaccion')
    def verificar_retencion(self):
        for rec in self:
            if rec.journal_id.type=='retencion' and rec.numero_transaccion:
                if rec.partner_id:
                    cobros = self.env['account.payment'].search([('partner_id','=',rec.partner_id.id),('numero_transaccion','=',rec.numero_transaccion)])
                    if cobros:
                        raise ValidationError('Retencion ya se encuentra cargada en el sistema. La misma se encuentra en fecha %s' % rec.payment_date)

    @api.onchange('banco_cheque_recibo')
    def _verficar_cuenta_banco_recibo(self):
        for rec in self:
            cuenta = self.env['res.partner.bank'].search([('partner_id', '=', rec.partner_id.id),('bank_id','=',rec.banco_cheque_recibo.id)])
            if cuenta:
                rec.ver_cuenta_banco_recibo=True
            else:
                rec.ver_cuenta_banco_recibo=False
                rec.titular_recibo=None
                rec.nro_cuenta_recibo=None




    @api.constrains('amount')
    def verificar_monto_cero_recibo(self):
        for rec in self:
            if rec.recibo_id:
                if rec.amount == 0 :
                    if rec.monto_cheque_recibo > 0:
                        rec.amount=rec.monto_cheque_recibo
                    else:
                        continue
                        # raise ValidationError('El cobro no  puede guardar con monto 0')


    @api.onchange('fecha')
    def verificar_fecha_pago_recibo(self):
        for rec in self:
            if rec.recibo_id:
                if rec.cheque_tercero:
                    if rec.recibo_id.fecha < rec.fecha:
                        rec.tipo_de_cheque_recibo='diferido'
                    else:
                        rec.tipo_de_cheque_recibo='vista'

    @api.depends('amount')
    def set_monto_cheque_recibo(self):
        if self.recibo_id:
            if not self.recibo_id.cobrar_dif_moneda and self.cheque_tercero:
                if self.currency_id != self.env.company.currency_id:
                    self.monto_cheque_recibo=round(self.amount,2)
                else:
                    self.monto_cheque_recibo=self.amount
            if not self.recibo_id.cobrar_dif_moneda:
                self.moneda_pago=self.currency_id



    @api.onchange('monto_cheque_recibo')
    def _set_monto_del_pago_recibo(self):
        for rec in self:
            # rec.amount=rec.monto_cheque_recibo
            rec.checks_amount=rec.monto_cheque_recibo
            if rec.recibo_id:
                if rec.recibo_id.cobrar_dif_moneda:
                    rec.monto_moneda_pago=rec.monto_cheque_recibo
                else:
                    rec.monto_moneda_pago=0


    @api.onchange('banco_cuenta_recibo')
    def _datos_cheque_recibo(self):
        for rec in self:
            cuenta=self.env['res.partner.bank'].search([('id','=',rec.banco_cuenta_recibo.id)])
            if cuenta:
                rec.nro_cuenta_recibo=cuenta.acc_number
                rec.titular_recibo=cuenta.titular_recibo
            else:
                rec.nro_cuenta_recibo = None
                rec.titular_recibo = None

    def cambiar_moneda(self):
        self.ensure_one()  # Asegurarse de que sólo se está trabajando con un solo registro

        # Ejecución de la consulta SQL para forzar el cambio de moneda
        if self.currency_id_tmp:
            query = """
                        UPDATE account_payment
                        SET currency_id = %s
                        WHERE id = %s
                    """
            self.env.cr.execute(query, (self.currency_id_tmp.id, self.id))

            # Invalidar la caché para que los cambios se reflejen inmediatamente en el ORM

        return True

    @api.depends('journal_id')
    def es_cheque_tercero(self):
        for rec in self:
            if rec.recibo_id:
                if rec.journal_id.payment_subtype:
                    if rec.journal_id.payment_subtype=='third_check':
                        rec.cheque_tercero=True
                        if rec.currency_id == self.env.company.currency_id:
                            rec.monto_cheque_recibo=rec.amount
                else:
                    rec.cheque_tercero=False
                    rec.nro_cuenta_recibo=None
                    rec.titular_recibo=None
                    rec.banco_cheque_recibo=None
                    rec.banco_cuenta_recibo=None
                    rec.fecha_cheque_recibo=None
                    rec.numero_cheque_recibo=None
                    # rec.monto_moneda_pago=None
                    rec.monto_cheque_recibo=None
                rec.cobrar_dif_moneda=rec.recibo_id.cobrar_dif_moneda
                if rec.recibo_id.currency_id == self.env.company.currency_id and rec.cobrar_dif_moneda:
                    rec.moneda_pago=self.env.company.currency_id
                elif rec.recibo_id.currency_id != self.env.company.currency_id and rec.cobrar_dif_moneda:
                    rec.moneda_pago = rec.recibo_id.currency_id
                if rec.recibo_id.dif_moneda:
                    rec.ver_monto_alternativo_2=True
                else:
                    rec.ver_monto_alternativo_2=False
                if rec.recibo_id.currency_invoice:
                    rec.currency_id=rec.recibo_id.currency_invoice
                else:
                    rec.currency_id=self.env.company.currency_id


    @api.depends('received_third_check_ids')
    def _calcular_cheque(self):
        for rec in self:
            if rec.recibo_id:
                for c in rec.received_third_check_ids:
                    rec.monto_cheque_recibo = c.amount
                    rec.banco_cheque_recibo=c.bank_id.name
                    rec.numero_cheque_recibo=c.number
                    if c.payment_date:
                        rec.fecha_cheque_recibo = c.payment_date
                    else:
                        rec.fecha_cheque_recibo = c.issue_date
