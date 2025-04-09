# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError, UserError
import calendar



class compania(models.Model):
    _inherit = 'res.company'

    cuenta_cheques_descontados = fields.Many2one('account.account',string="Cuenta de Cheques Descontados",help="Esta cuenta se utiliza para el modulo de descuento de cheques")
    cuenta_avales_otorgados = fields.Many2one('account.account',string="Cuenta Avales Otorgados",help="Esta cuenta se utiliza para el modulo de descuento de cheques")



class cheques_terceros(models.Model):

    _inherit = 'account.check.third'

    descuento_id = fields.Many2one('descuento.cheques', string="Nro. de Descuento", ondelete="set null")

    state = fields.Selection(selection_add=[('descontado', 'Descontado')], ondelete={'descontado': 'cascade'})
    asiento_descuento = fields.Many2one('account.move',string='Asiento de Descuento')












class descuento_cheques (models.Model):

    _name = 'descuento.cheques'
    _inherit = ['mail.thread']


    name = fields.Char (string='Boleta Descuento Nro.', required = True ,track_visibility='onchange')
    cuenta = fields.Many2one('account.journal',string="Cuenta a Depositar", required=True ,track_visibility='onchange')
    monto_a_depositar = fields.Monetary(currency_field='currency_id', string="Total de Cheques", compute= '_monto_a_depositar' )
    currency_id = fields.Many2one('res.currency',string="Moneda", default = lambda self: self.env.company.currency_id, required=True ,track_visibility='onchange')
    cheques = fields.One2many('account.check.third','descuento_id',string="Cheques a Depositar", ondelete="set null")
    asiento_contable = fields.Many2one ('account.move',string="Asiento Generado",track_visibility='onchange')
    asiento_contable_envio = fields.Many2one ('account.move',string="Asiento Generado Envio al Banco",track_visibility='onchange')
    fecha  = fields.Date (string="Fecha de Descuento",default = str(datetime.today()),track_visibility='onchange')
    state = fields.Selection({('borrador', 'Borrador'),('enviado','Enviado al Banco'),('confirmado', 'Confirmado'), ('anulado', 'Anulado')},
                             string="Estado", default='borrador',track_visibility='onchange')
    diario_provision_intereses = fields.Many2one('account.journal',string="Diario de Provision de Intereses")
    total_depositado = fields.Float(string="Total Depositado en Banco")
    company_id = fields.Many2one('res.company',string="Company",default = lambda self: self.env.company)
    # monto_depositado = fields.Monetary(related="monto_a_depositar",string="Total")


    def unlink(self):
        if self.state != 'borrador':
            raise ValidationError('No se puede eliminar un registro que no este en estado borrador')
        res = super(descuento_cheques, self).unlink()
        return res



    def check_checks(self):
        fec = datetime.today()
        numeros = ''
        cheques_terce = self.env['account.check.third'].search([('payment_date', '=', fec), ('state', '=', 'descontado')])

        # raise ValidationError ('aaa %s' % cheques_terces)
        # fechas = datetime.strptime(str(datetime.now()), '%Y-%m-%d')
        fecha = datetime.strftime(fec, "%Y/%m/%d")

        credito = []
        debito = []
        journal = self.env['account.journal'].search([('company_id','=',self.env.company.id),('type','=','general')],limit=1)
        move_line = self.env['account.move.line']
        cred_moneda = 0

        monto_total = 0
        monto_mon_ex = 0
        seq_id = self.env['ir.sequence'].search([('id', '=', journal.sequence_id.id)])
        name = seq_id._next()
        ref = 'Deposito de cheques descontados en fecha ' + str(fecha)


        if cheques_terce:
            move_vals = {
                'name': name,
                'journal_id': journal.id,
                'date': fecha,
                'ref': ref,
            }
            move = self.env['account.move'].with_context({}).create(move_vals)
            cred_moneda = 0
            for monedas in cheques_terce.mapped('currency_id'):
                    numeros = ''
                    cheques_a_depo = cheques_terce.filtered(lambda record : record.currency_id == monedas)



                    if monedas != self.env.company.currency_id:
                        moneda_ex = 1

                    else:
                        moneda_ex = 0

                    numeros_de_cheques = cheques_a_depo.mapped('number')
                    for num in numeros_de_cheques:
                        numeros = numeros + ' ' + str(num) + ','
                    monto_de_mon = sum(cheques_a_depo.mapped('amount'))


                    if moneda_ex == 1:
                        monto_ex = self.currency_id.with_context(name=fecha).compute(monto_de_mon,
                                                                                          self.env.company.currency_id)
                        monto_moneda = -1 * monto_de_mon
                        deb_mon = monto_de_mon
                        cred_moneda = monto_de_mon

                    else:
                        monto_ex = monto_de_mon
                        monto_moneda = 0
                        deb_mon = 0
                        cred_moneda = 0
                    monto_total += monto_ex
                    print(monto_ex)
                    credi = {
                        'name': 'Cheque' + numeros,
                        'account_id': self.env.company.cuenta_cheques_descontados.id,
                        'move_id': move.id,
                        'debit': 0,
                        'currency_id': monedas.id,
                        'amount_currency': monto_moneda,
                        'credit': monto_ex,
                        # 'ref': 'Cheques' + numeros,
                    }
                    credito.append(credi)
                    move.line_ids.with_context(check_move_validity=False).create(credi)

                    debi = {
                        # 'name': name,
                        'account_id': self.env.company.cuenta_avales_otorgados.id,
                        'move_id': move.id,
                        'debit': monto_ex,
                        'currency_id': monedas.id,
                        'amount_currency': deb_mon,
                        'credit': 0,
                        'name': 'Cheque' + numeros,
                    }
                    debito.append(debi)
                    move.line_ids.with_context(check_move_validity=False).create(debi)
                # lineas += debi
                # move.line_ids += lineas

            move.post()
            for chequi in cheques_terce:
                chequi.write({'deposit_account_move_id': move.id, 'state': 'deposited'})


        return True

        # raise ValidationError('aa %s' % cheques)



    @api.depends('cheques')

    def _monto_a_depositar(self):
        monto = 0

        if self.cheques:
            for cheques in self.cheques:
                monto += cheques.amount



        self.monto_a_depositar = monto




    def anular(self):

        self.total_depositado = 0

        for move in self.cheques.mapped('asiento_descuento'):

            move.button_cancel()
            move.unlink()

        for cheque in self.cheques:
            if cheque.state=='deposited':
                raise ValidationError ('No puede anular  un descuento de un cheque que ya se encuentra depositado')
            cheque.write({'state':'handed'})


        if self.asiento_contable:
            if self.asiento_contable.state == 'posted':
                self.asiento_contable.button_cancel()
            self.asiento_contable.unlink()
        if self.asiento_contable_envio:
            if self.asiento_contable_envio.state == 'posted':
                self.asiento_contable_envio.button_cancel()
            self.asiento_contable_envio.unlink()


        self.state = 'anulado'


    def pasar_borrador(self):
        self.state='borrador'


    # @api.onchange('tipo_deposito')
    # def cambio_tipo(self):
    #     if self.tipo_deposito:
    #         if self.tipo_deposito=='cheque':
    #             self.depositos = None
    #         else:
    #             self.cheques = None


    def enviar(self):

        if not self.env.company.cuenta_cheques_descontados:
            raise ValidationError ('No se encuentra configurada la cuenta para cheques descontados. Para configurarla debe ir a la informacion de su compañia y agregarla alli ')
        credito = []
        debito = []
        journal = self.cuenta
        move_line = self.env['account.move.line']
        cred_moneda = 0
        if self.currency_id != self.env.company.currency_id:
            moneda_ex = 1
        else:
            moneda_ex = 0
        monto_total = 0
        seq_id = self.env['ir.sequence'].search([('id', '=', journal.sequence_id.id)])
        name = seq_id._next()
        ref = 'Envio al Banco segun Desc. Nro. ' + self.name
        # if self.tipo_deposito=='cheque':
        cuentas = self.cheques.mapped('cuenta_origen')
        if not self.cheques:
            raise ValidationError('Debe seleccionar al menos un cheque a descontar')
        # else:
        #     if not self.depositos:
        #         raise ValidationError('Debe seleccionar al menos un cobro de efectivo a depositar')
        #     cuentas = self.depositos.mapped('account_id')
        # raise ValidationError ('aaa %s' % len(cuentas))
        if cuentas:
            move_vals = {
                'name': name,
                'journal_id': journal.id,
                'date': self.fecha,
                'ref': ref,
            }
            move = self.env['account.move'].with_context({}).create(move_vals)
            for cuenta in cuentas:
                monto_cred = 0


                for cheque in self.cheques:
                    if cheque.cuenta_origen == cuenta:
                        monto_cred += cheque.amount


                if moneda_ex == 1:
                    monto_ex = self.currency_id.with_context(name=self.fecha).compute(monto_cred,
                                                                                      self.env.company.currency_id)
                    monto_moneda = -1 * monto_cred
                    cred_moneda += monto_cred

                else:
                    monto_ex = monto_cred
                    monto_moneda = 0
                    cred_moneda += 0
                monto_total += monto_ex
                print(monto_ex)
                credi = {
                    'name': name,
                    'account_id': cuenta.id,
                    'move_id': move.id,
                    'debit': 0,
                    'currency_id': self.currency_id.id,
                    'amount_currency': monto_moneda,
                    'credit': monto_ex,
                    'ref': ref,
                }
                credito.append(credi)
                move.line_ids.with_context(check_move_validity=False).create(credi)
                # lineas = move_line.with_context({}).create(credi)
                # lineas = credi

            print('debit')
            print(cred_moneda)
            debi = {
                'name': name,
                'account_id': self.env.company.cuenta_cheques_descontados.id,
                'move_id': move.id,
                'debit': monto_total,
                'currency_id': self.currency_id.id,
                'amount_currency': cred_moneda,
                'credit': 0,
                'ref': ref,
            }
            debito.append(debi)
            move.line_ids.with_context(check_move_validity=False).create(debi)
            # lineas += debi
            # move.line_ids += lineas

            move.post()

            self.state = 'enviado'
            self.asiento_contable_envio = move.id



    def confirmar(self):
        credito = []
        debito = []
        journal = self.cuenta
        move_line = self.env['account.move.line']
        cred_moneda = 0
        if self.currency_id != self.env.company.currency_id:
            moneda_ex=1
        else:
            moneda_ex=0
        monto_total = 0
        seq_id = self.env['ir.sequence'].search([('id', '=', journal.sequence_id.id)])
        name = seq_id._next()
        ref= 'Desembolso Descuento Nro. '+ self.name
        # if self.tipo_deposito=='cheque':
        cuentas = self.env.company.cuenta_avales_otorgados
        if not self.env.company.cuenta_avales_otorgados:
            raise ValidationError ('No se encuentra configurada la cuenta para avales otorgados. Para configurarla debe ir a la informacion de su compañia y agregarla alli ')
        if not self.cheques:
            raise ValidationError ('Debe seleccionar al menos un cheque a depositar')
        # else:
        #     if not self.depositos:
        #         raise ValidationError('Debe seleccionar al menos un cobro de efectivo a depositar')
        #     cuentas = self.depositos.mapped('account_id')
        # raise ValidationError ('aaa %s' % len(cuentas))
        if cuentas:
            move_vals = {
                'name': name,
                'journal_id': journal.id,
                'date': self.fecha,
                'ref': ref,
            }
            move = self.env['account.move'].with_context({}).create(move_vals)
            cuenta = cuentas
            monto_cred=0


            for cheque in self.cheques:

                monto_cred += cheque.amount

            if self.total_depositado == 0:
                raise ValidationError('El total depositado no puede ser 0')

            if not self.diario_provision_intereses:
                raise ValidationError ('Debe seleccionar el diario donde irá la provision de intereses')

            if self.total_depositado > monto_cred:
                raise ValidationError ('El total depositado no puede ser mayor a la suma de todos los cheques')

            if moneda_ex==1:
                monto_ex = self.currency_id.with_context(name=self.fecha).compute(monto_cred,self.env.company.currency_id)
                monto_moneda = -1 * monto_cred
                cred_moneda += monto_cred

            else:
                monto_ex = monto_cred
                monto_moneda = 0
                cred_moneda += 0
            monto_total += monto_ex
            print (monto_ex)
            credi= {
                'name': name,
                'account_id': cuenta.id,
                'move_id': move.id,
                'debit': 0,
                'currency_id': self.currency_id.id,
                'amount_currency': monto_moneda ,
                'credit': monto_ex,
                'ref': ref,
            }
            credito.append(credi)
            move.line_ids.with_context(check_move_validity=False).create(credi)
            # lineas = move_line.with_context({}).create(credi)
            # lineas = credi

            print('debit')
            print(cred_moneda)

            if moneda_ex == 1:
                monto_ex = self.currency_id.with_context(name=self.fecha).compute(self.total_depositado,
                                                                                  self.env.company.currency_id)
                monto_moneda = monto_cred
                deb_moneda = self.total_depositado

            else:
                monto_ex = self.total_depositado
                monto_moneda = 0
                deb_moneda = 0

            debi = {
                'name': name,
                'account_id': journal.default_debit_account_id.id,
                'move_id': move.id,
                'debit': monto_ex,
                'currency_id': self.currency_id.id,
                'amount_currency': deb_moneda ,
                'credit': 0,
                'ref': ref,
            }
            debito.append(debi)
            move.line_ids.with_context(check_move_validity=False).create(debi)

            if moneda_ex == 1:
                monto_ex = self.currency_id.with_context(name=self.fecha).compute((monto_cred - self.total_depositado),
                                                                                  self.env.company.currency_id)
                monto_moneda = monto_cred
                deb_moneda = monto_cred - self.total_depositado

            else:
                monto_ex = monto_cred - self.total_depositado
                monto_moneda = 0
                deb_moneda = 0

            debi = {
                'name': name,
                'account_id': self.diario_provision_intereses.default_debit_account_id.id,
                'move_id': move.id,
                'debit': monto_ex,
                'currency_id': self.currency_id.id,
                'amount_currency': deb_moneda,
                'credit': 0,
                'ref': ref,
            }


            debito.append(debi)
            move.line_ids.with_context(check_move_validity=False).create(debi)
            # lineas += debi
            # move.line_ids += lineas

            move.post()
            # if self.tipo_deposito=='cheque':
            for cheque in self.cheques:
                cheque.write({'asiento_descuento':move.id,'state':'descontado'})
                cheque.message_post(_(
                    'Ha sido descontado segun descuento Nro. <a href=# data-oe-model=descuento.cheques data-oe-id=%d>%s</a> .') % (
                                    self.id, self.name))
            # else:
            #     for depo in self.depositos:
            #         depo.write({'depositado_efe':True})
            self.state = 'confirmado'
            self.asiento_contable = move.id

