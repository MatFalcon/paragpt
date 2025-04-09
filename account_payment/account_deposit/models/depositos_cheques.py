# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError, UserError
import calendar
import logging

_logger = logging.getLogger(__name__)

# class pos_sess(models.Model):
#     _inherit = 'pos.session'
#
#     deposito = fields.Many2one('depositos.cheques',string="Boleta de Deposito", ondelete="set null")

class cheques_terceros(models.Model):

    _inherit = 'account.check.third'

    deposito_id = fields.Many2one('depositos.cheques', string="Boleta de Deposito",tracking=True)
    fecha_deposito = fields.Date(related='deposito_id.fecha')




    def unlink (self):
        if self.deposito_id:
            if self.deposito_id.state == 'confirmado':
                raise ValidationError ('No puede eliminar un cheque que posee una boleta de deposito en estado confirmado ')
            else:
                self.deposito_id = None
        else:
            super(cheques_terceros, self).unlink()


class linea_asiento(models.Model):
    _inherit = 'account.move.line'


    boleta_deposito_id = fields.Many2one('depositos.cheques',string="Boleta de Deposito")
    depositado_efe = fields.Boolean (string="Depositado",default= False)

    #
    # def _update_check(self):
    #     """ Raise Warning to cause rollback if the move is posted, some entries are reconciled or the move is older than the lock date"""
    #     move_ids = set()
    #     for line in self:
    #         err_msg = _('Move name (id): %s (%s)') % (line.move_id.name, str(line.move_id.id))
    #         params = dict(self._context.get('params') or {})
    #         if params['model'] != 'depositos.cheques':
    #             if line.move_id.state != 'draft':
    #                 raise UserError(_(
    #                     'You cannot do this modification on a posted journal entry, you can just change some non legal fields. You must revert the journal entry to cancel it.\n%s.') % self._context)
    #             if line.reconciled and not (line.debit == 0 and line.credit == 0):
    #                 raise UserError(_(
    #                     'You cannot do this modification on a reconciled entry. You can just change some non legal fields or you must unreconcile first.\n%s.') % err_msg)
    #         if line.move_id.id not in move_ids:
    #             move_ids.add(line.move_id.id)
    #     self.env['account.move'].browse(list(move_ids))._check_lock_date()
    #     return True


    def unlink(self):
        for linea in self:
            if linea.boleta_deposito_id:
                if linea.boleta_deposito_id.state == 'confirmado':
                    raise ValidationError ('No puede borrar una linea de asiento que hay sido depositado')
                else:
                    linea.boleta_deposito_id = None
                    linea.depositado_efe = False
        super(linea_asiento,self).unlink()


class depositos_cheques (models.Model):

    _name = 'depositos.cheques'
    _inherit = ['mail.thread']


    name = fields.Char (string='Boleta Nro.', required = True ,tracking=True)
    cuenta = fields.Many2one('account.journal',string="Cuenta a Depositar", required=True ,tracking=True)
    monto_a_depositar = fields.Monetary(currency_field='currency_id', string="Monto a Depositar", compute= '_monto_a_depositar' )
    currency_id = fields.Many2one('res.currency',string="Moneda",  required=True ,tracking=True)
    cheques = fields.One2many('account.check.third','deposito_id',string="Cheques a Depositar")
    asiento_contable = fields.Many2one ('account.move',string="Asiento Generado",tracking=True)
    fecha  = fields.Date (string="Fecha de Deposito",default=lambda self: fields.Date.context_today(self),tracking=True)
    state = fields.Selection(selection=[('borrador', 'Borrador'), ('confirmado', 'Confirmado'), ('anulado', 'Anulado')],
                             string="Estado", default='borrador',tracking=True)
    # monto_depositado = fields.Monetary(related="monto_a_depositar",string="Total")
    depositos = fields.One2many('account.move.line', 'boleta_deposito_id')
    tipo_deposito = fields.Selection(selection=[
        ('efectivo', 'Efectivo'),
        ('cheque', 'Cheque'),
        ('manual', 'Manual')],string="Tipo de Deposito", default='cheque',tracking=True)
    journal_from = fields.Many2one('account.journal', string="Depositar Desde",tracking=True)
    cuenta_from = fields.Many2one('account.account', related='journal_from.default_account_id',string="Cuenta desde",tracking=True)
    monto_manual = fields.Float(currency_field='currency_id', string="Monto a Depositar",tracking=True)
    # check_cajas = fields.Boolean(string='Ver listado de Cajas',default=False)
    # cajas = fields.One2many('pos.session', 'deposito', string='Cajas', ondelete="set null")
    company_id = fields.Many2one('res.company', 'Company', required=True,default=lambda self: self._get_default_company())
    forzar_origen = fields.Boolean(string="Definir Cuenta Origen",tracking=True)
    obs= fields.Text(string="Observaciones", help="Nombre que se utilizará en los apuntes contables",tracking=True)
    fecha_cobro=fields.Date()
    moneda_extranjera=fields.Boolean(compute='_set_moneda_extranjera')



    @api.depends('currency_id')
    def _set_moneda_extranjera(self):
        if len(self)==1:
            if self.currency_id != self.env.company.currency_id:
                self.moneda_extranjera=True
            else:
                self.moneda_extranjera=False

    @api.onchange('cheques','depositos')
    def setear_fecha_cobro(self):
        if self.moneda_extranjera:
            if self.cheques:
                cheque=self.cheques[0]
                if cheque.voucher_id:
                    self.fecha_cobro=cheque.voucher_id.date
            elif self.depositos:
                deposito=self.depositos[0]
                self.fecha_cobro=deposito.date
            else:
                self.fecha_cobro=None


    @api.constrains('name')
    def control_duplicado(self):
        if self.name:
            deposito=self.env['depositos.cheques'].search([('name','=',self.name)])
            print(len(deposito))
            if len(deposito)>1:
                raise ValidationError('El numero de deposito ya esta cargado favor verifique')


    
    def _get_default_company(self):
        return self.env.company.id

    @api.onchange('monto_a_depositar')
    def cambio_monto_a_depositar(self):
        self.monto_manual = self.monto_a_depositar

    #
    # def check_caj(self):
    #     for a in self:
    #         a.check_cajas= True
    #
    # @api.onchange('cajas')
    # def traer_efectivo(self):
    #
    #         # self.check_depo()
    #
    #         self.depositos = None
    #         new_lines = list()
    #         # context = dict(self._context or {})
    #
    #         # context['allow_amount_currency'] = True
    #         # context['skip_verif'] = True
    #         if self.cajas:
    #
    #             for act in self.cajas:
    #
    #                 for statement in act.statement_ids:
    #                     if statement.journal_id.type=='cash':
    #                         for line in statement.move_line_ids:
    #                             if  line.account_id.user_type_id.type=='liquidity':
    #                                 # line.move_id.button_cancel()
    #                                 new_lines.append(line.id)
    #                                 # self.depositos += line.with_context(allow_amount_currency=True,skip_verif=True)
    #                 self.depositos = [(6,0,new_lines)]

    @api.depends('cheques','depositos')
    def _monto_a_depositar(self):
        for rec in self:
            monto = 0
            if rec.cheques:
                for cheques in rec.cheques:
                    monto += cheques.amount
            if rec.depositos:
                for depositos in rec.depositos:
                    if depositos.amount_currency > 0 and depositos.currency_id != self.env.company.currency_id:
                        monto += depositos.amount_currency
                    else:
                        if depositos.debit > 0:
                            monto += depositos.debit
                        if depositos.credit > 0:
                            monto -= depositos.credit

            rec.monto_a_depositar = monto


    def anular(self):
        if self.tipo_deposito =='cheque':


                for move in self.cheques.mapped('deposit_account_move_id'):

                    move.button_cancel()
                    move.with_context(check_move_validity=False).unlink()

                for cheque in self.cheques:
                    cheque.write({'state':'handed'})
        else:
            for depo in self.depositos:
                depo.depositado_efe = False

        if self.asiento_contable.state == 'posted':
            self.asiento_contable.button_cancel()
        self.asiento_contable.unlink()


        self.state = 'anulado'


    def pasar_borrador(self):
        self.state='borrador'


    @api.onchange('tipo_deposito')
    def cambio_tipo(self):
        if self.tipo_deposito:
            if self.tipo_deposito == 'cheque':
                self.depositos = None
                self.monto_manual = 0
            elif self.tipo_deposito == 'manual':
                self.cheques = None
                self.depositos = None
            else:
                self.cheques = None
                self.monto_manual = 0
                
    @api.onchange('depositos')
    def agregar_depos(self):
        monto = 0

        if self.depositos:
            for depositos in self.depositos:
                monto += depositos.debit

        self.monto_manual = monto

    
    def confirmar(self):
        credito = []
        debito = []
        journal = self.cuenta
        move_line = self.env['account.move.line']
        cred_moneda = 0
        if self.currency_id != self.env.company.currency_id:
            moneda_ex=1
            if not self.fecha_cobro:
                raise ValidationError('Favor agregue la fecha de cobro para poder realizar el asiento de diferencia de cambio')
            tasa_cobro = self.env['res.currency.rate'].search(
                [('company_id', '=', self.env.company.id), ('currency_id', '=', self.currency_id.id),
                 ('name', '=', self.fecha_cobro)])
            monto_tasa = 1
            if not tasa_cobro:
                raise ValidationError('No se encuentra cotizacion cargada para la fecha %s' % self.fecha_cobro)
            else:
                monto_tasa_dif = tasa_cobro[0].set_venta
            tasa = self.env['res.currency.rate'].search(
                [('company_id', '=', self.env.company.id), ('currency_id', '=', self.currency_id.id),
                 ('name', '=', self.fecha)])
            if not tasa:
                raise ValidationError('No se encuentra cotizacion cargada para la fecha %s' % self.fecha)
            else:
                monto_tasa_2 = tasa[0].set_venta
            diferencia=0
            if tasa_cobro.set_venta<tasa.set_venta:
                diferencia=1
            valor_monto=0
            if self.monto_manual >0:
                valor_monto=self.monto_manual
            elif self.monto_a_depositar>0:
                valor_monto=self.monto_a_depositar
            valor_diferencia=abs(monto_tasa_2*valor_monto-monto_tasa_dif*valor_monto)
            if self.tipo_deposito == 'efectivo':
                suma_depo= sum([ depo.amount_currency   for depo in self.depositos if depo.currency_id != self.env.company.currency_id and depo.amount_currency > 0])

        else:
            moneda_ex=0
        monto_total = 0
        if self.obs:
            ref= self.obs
        else:
            ref = 'Deposito Boleta Nro. ' + self.name + ' '
        if self.tipo_deposito=='cheque':
            if not self.forzar_origen:
                cuentas = self.cheques.mapped('cuenta_origen')
            else:
                if not self.journal_from:
                    raise ValidationError('Debe seleccionar Diario de Origen')
                if not self.journal_from.default_account_id:
                    raise ValidationError('El diario debe contener cuenta deudora')
                cuentas = self.journal_from.default_account_id
            if not self.cheques:
                raise ValidationError ('Debe seleccionar al menos un cheque a depositar')
        elif self.tipo_deposito == 'manual':
            cuentas = self.journal_from.default_account_id
        else:
            if not self.depositos:
                raise ValidationError('Debe seleccionar al menos un cobro de efectivo a depositar')
            cuentas = self.depositos.mapped('account_id')
        # raise ValidationError ('aaa %s' % len(cuentas))
        if cuentas:
            move_vals = {
                'journal_id': journal.id,
                'date': self.fecha,
                'ref': ref,
            }
            move = self.env['account.move'].with_context({}).create(move_vals)
            for cuenta in cuentas:
                monto_cred=0
                cred_moneda=0
                if self.tipo_deposito=='cheque':
                    for cheque in self.cheques:
                        if not self.forzar_origen:
                            if cheque.cuenta_origen == cuenta:
                                monto_cred += cheque.amount
                        else:
                            monto_cred += cheque.amount
                        
                elif self.tipo_deposito == 'manual':
                    monto_cred += self.monto_manual
                else:
                    for depo in self.depositos:
                        if depo.account_id == cuenta:
                            if depo.currency_id != self.env.company.currency_id and depo.amount_currency > 0:
                                monto_cred += depo.amount_currency
                            else:

                                monto_cred += (depo.debit - depo.credit)

                if moneda_ex == 1:
                    tasa = self.env['res.currency.rate'].search(
                        [('company_id', '=', self.env.company.id), ('currency_id', '=', self.currency_id.id),
                         ('name', '=', self.fecha)])
                    if not tasa:
                        raise ValidationError('No se encuentra cotizacion cargada para la fecha %s' % self.fecha)
                    else:
                        monto_tasa = tasa[0].set_venta
                    # monto_ex = self.currency_id.with_context(name=self.fecha).compute(monto_cred,self.env.company.currency_id)
                    prorrateo=0
                    porcen=1
                    if self.tipo_deposito=='efectivo':
                        if suma_depo>0:
                            porcen=monto_cred/suma_depo
                        prorrateo=valor_diferencia*porcen
                    else:
                        prorrateo=valor_diferencia
                    if diferencia==1:
                        monto_ex = monto_tasa * monto_cred - prorrateo
                    else:
                        print('valor_monto',valor_monto)
                        print('monto_tasa',monto_tasa)
                        monto_ex = tasa_cobro.set_venta * valor_monto
                    monto_moneda = -1 * monto_cred*porcen
                    cred_moneda += monto_cred
                    monto_total_dif_cambio=valor_monto*tasa_cobro.set_venta
                    monto_total=valor_monto*tasa.set_venta
                else:
                    monto_ex = monto_cred
                    monto_moneda = 0
                    cred_moneda += 0
                    monto_total += monto_ex
             
                credi= {
                    'name': 'Deposito Boleta Nro. '+ self.name + ' ' + (self.obs or ''),
                    'account_id': cuenta.id,
                    'move_id': move.id,
                    'debit': 0,
                    'currency_id': self.currency_id.id,
                    'amount_currency': -monto_ex ,
                    'credit': monto_ex,
                    'ref': ref,
                }
                credito.append(credi)
                move.line_ids.with_context(check_move_validity=False).create(credi)
                # lineas = move_line.with_context({}).create(credi)
                # lineas = credi
            if moneda_ex == 1:
                if valor_diferencia != 0:
                    # journal_dif_cambio=self.env['account.journal'].search([('exchange_rate_journal','=',True),('company_id','=',self.env.company.id)])
                    
                    if diferencia==1:
                        credi= {
                            'name': 'Deposito Boleta Nro. '+ self.name + ' ' + (self.obs or ''),
                            # 'account_id': journal_dif_cambio.default_account_id.id,
                            'account_id': self.env.company.income_currency_exchange_account_id.id,
                            'move_id': move.id,
                            'debit': 0,
                            'credit': valor_diferencia,
                            'ref': ref,
                        }
                        credito.append(credi)
                        move.line_ids.with_context(check_move_validity=False).create(credi)
                    else:
                        debi = {
                            'name': 'Deposito Boleta Nro. ' + self.name + ' ' + (self.obs or ''),
                            # 'account_id': journal_dif_cambio.default_account_id.id,
                            'account_id': self.env.company.expense_currency_exchange_account_id.id,
                            'move_id': move.id,
                            'debit': valor_diferencia,
                            'credit': 0,
                            'ref': ref,
                        }
                        debito.append(debi)
                        move.line_ids.with_context(check_move_validity=False).create(debi)

            # if  valor_diferencia  > 0:
            #     monto_total -= valor_diferencia
            sum_credi = sum(l['credit'] for l in credito)
            sum_debi = sum(l['debit'] for l in debito)
            valor_final = abs(sum_credi - sum_debi)
            debi = {
                'name': 'Deposito Boleta Nro. '+ self.name + ' ' + (self.obs or ''),
                'account_id': journal.default_account_id.id,
                'move_id': move.id,
                'debit': valor_final,
                'currency_id': self.currency_id.id,
                'amount_currency': valor_final ,
                'credit': 0,
                'ref': ref,
            }
            debito.append(debi)
            move.line_ids.with_context(check_move_validity=False).create(debi)
            # lineas += debi
            # move.line_ids += lineas

            move.action_post()

            if self.tipo_deposito=='cheque':
                for cheque in self.cheques:
                    msg = _("Ha sido depositado segun boleta Nro. <a href=# data-oe-model=depositos.cheques data-oe-id=%d>%s</a> .") % (self.id, self.name)
                    cheque.write({'deposit_account_move_id':move.id,'state':'deposited'})
                    cheque.message_post(body=msg)

            else:
                for depo in self.depositos:
                    depo.write({'depositado_efe':True})
            self.state = 'confirmado'
            self.asiento_contable = move.id

    def agregar_punto_de_miles(self,numero):
        entero=int(numero)
        decimal='{0:.3f}'.format(numero-entero)
        entero_string='.'.join([str(int(entero))[::-1][i:i+3] for i in range(0,len(str(int(entero))),3)])[::-1]
        if decimal == '0.000':
            numero_con_punto=entero_string
        else:
            decimal_string=str(decimal).split('.')
            numero_con_punto=entero_string+','+decimal_string[1]
        return numero_con_punto
