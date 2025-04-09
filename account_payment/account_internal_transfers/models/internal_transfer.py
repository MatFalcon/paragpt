# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError, UserError

import calendar
import logging

_logger=logging.getLogger(__name__)
class trasnferencias(models.Model):

    _name='transferencias.entre.cuentas'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name= fields.Char(string="Nro Transferencia",track_visibility="onchange")
    cuenta_origen = fields.Many2one('account.journal',string="Cuenta Origen",track_visibility="onchange",required=True)
    transitoria_origen = fields.Boolean(string="Utilizar cuenta transitoria de Origen",default=False)
    cuenta_destino = fields.Many2one('account.journal',string="Cuenta Destino",track_visibility="onchange",required=True)
    transitoria_destino=fields.Boolean(string="Utilizar cuenta transitoria de destino",default=False)
    state = fields.Selection(selection=[('borrador', 'Borrador'), ('confirmado', 'Confirmado'), ('anulado', 'Anulado')],
                             string="Estado", default='borrador',track_visibility="onchange")
    check_id = fields.Many2one('account.check',string="Cheque",track_visibility="onchange")
    type_journal = fields.Selection(related='cuenta_origen.payment_subtype')
    monto = fields.Monetary(string="Cantidad", currency_field='currency_id', required=True,track_visibility="onchange")
    currency_id = fields.Many2one('res.currency', string="Moneda",required=True)
    fecha = fields.Date(string="Fecha de Operacion",required=True,track_visibility="onchange")
    move_id = fields.Many2one('account.move', string="Asiento contable")
    tasa_cambio = fields.Float(string='Tasa de Cambio Bancaria',track_visibility="onchange")
    observacion = fields.Text(string='Observaciones',track_visibility="onchange", help="Nombre que se utilizará en los apuntes contables")
    company_id = fields.Many2one('res.company',string="Compañia",default=lambda self: self._get_default_compania())
    exchange_account_id= fields.Many2one('account.account',string="Cuenta Diferencia de Cambio",track_visibility="onchange")
    crear_diferencia_cambio = fields.Boolean(default=False,string="Crear asiento diferencia de cambio",track_visibility="onchange")
    currency_dest_id = fields.Many2one('res.currency',string="Moneda destino",track_visibility="onchange")
    diferencia_cambio = fields.Float(string="Diferencia de Cambio")


    # lineas_movimientos_ids = fields.One2many('ruc.caja.detalle.egreso', 'transferencia_id', string="Líneas de Movimientos")

    @api.onchange('crear_diferencia_cambio')
    def _set_exchange_account_id(self):
        for rec in self:
            dif_cambio = 0
            diferencia_cambio_diario = self.env['account.journal'].search([('exchange_rate_journal','=',True),('company_id','=',rec.env.user.company_id.id)])
            if len(diferencia_cambio_diario) > 0:
                if rec.tasa_cambio > 0:

                    if rec.currency_id != self.env.company.currency_id:
                        suma = round(rec.monto * rec.tasa_cambio)
                        if rec.crear_diferencia_cambio:
                            rate_origen = self.env['res.currency.rate'].search(
                                [('currency_id', '=', rec.currency_id.id), ('name', '=', rec.fecha)])
                            cot_origen = rate_origen.set_venta
                            if rec.currency_dest_id != rec.env.user.company_id.currency_id:
                                amount = rec.currency_dest_id._convert(suma, self.env.company.currency_id, date=rec.fecha)
                                dif_cambio += amount - (cot_origen * rec.monto)
                            else:
                                dif_cambio += suma - (cot_origen * rec.monto)

                    elif rec.currency_dest_id != rec.env.user.company_id.currency_id:
                        dif_cambio_ex = 0
                        dif_cambio = 0
                        suma = round(rec.monto / rec.tasa_cambio, 2)
                        if self.crear_diferencia_cambio:
                            rate_destino = self.env['res.currency.rate'].search(
                                [('currency_id', '=', rec.currency_dest_id.id), ('name', '=', rec.fecha)])
                            cot_destino = rate_destino.set_venta
                            dif_cambio_ex += suma - (rec.monto / cot_destino)
                            dif_cambio += dif_cambio_ex * cot_destino

                    rec.diferencia_cambio = round(dif_cambio)


                else:
                    ValidationError(
                        'Si va a realizar una transferencia entre cuentas de Diferentes monedas debe cargar la tasa de cambio')
                if rec.diferencia_cambio > 0:
                    rec.exchange_account_id = diferencia_cambio_diario[0].default_account_id
                else:
                    rec.exchange_account_id = diferencia_cambio_diario[0].default_account_id

    # codigo para reporte

    def transfer_value(self):
        for rec in self:
            monto=0
            if rec.move_id:
                lineas = rec.move_id.line_ids
                if lineas:
                    for l in lineas:
                        if rec.cuenta_destino.default_account_id == l.account_id:
                            if l.currency_id:
                                if l.currency_id != rec.env.user.company_id.currency_id:
                                    monto = l.amount_currency
                                else:
                                    monto = l.debit + l.credit
                            else:
                                monto = l.debit + l.credit
            return monto

    def set_currency(self):
        for rec in self:
            moneda=[]
            if rec.move_id:
                lineas = rec.move_id.line_ids
                if lineas:
                    for l in lineas:
                        if rec.cuenta_destino.default_account_id == l.account_id:
                            if l.currency_id:
                                if l.currency_id != rec.env.user.company_id.currency_id:
                                    moneda = l.currency_id
                                else:
                                    moneda = rec.env.user.company_id.currency_id
                            else:
                                moneda = rec.env.user.company_id.currency_id
            return moneda

    def agregar_punto_de_miles(self, numero, moneda):
        numero_con_punto = 0
        if moneda:
            if 'USD' in moneda.name:
                entero = int(numero)
                decimal = '{0:.2f}'.format(numero - entero)
                entero_string = '.'.join([str(int(entero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                                ::-1]
                if decimal == '0.00':
                    numero_con_punto = entero_string
                else:
                    decimal_string = str(decimal).split('.')
                    numero_con_punto = entero_string + ',' + decimal_string[1]
            else:
                numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(numero))), 3)])[
                               ::-1]
        return numero_con_punto
    # fin del codigo para reporte

    @api.onchange('cuenta_origen','cuenta_destino')
    def obtener_monedas(self):
        if self.cuenta_origen:
            if self.cuenta_origen.currency_id:
                self.currency_id = self.cuenta_origen.currency_id
            else:
                self.currency_id = self.env.company.currency_id
        if self.cuenta_destino:
            if self.cuenta_destino.currency_id:
                self.currency_dest_id = self.cuenta_destino.currency_id
            else:
                self.currency_dest_id = self.env.company.currency_id


    
    def _get_default_compania(self):
        company = self.env.company
        return company


    def unlink(self):
        if self.state =='confirmado':
            raise ValidationError ('No puede borrar un registro que esté en estado Confirmado ')
        else:
            res = super(trasnferencias,self).unlink()
            return res

    def anular(self):

        if self.state == 'confirmado':
            if self.cuenta_origen.caja_chica:
                caja_detalle_egreso = self.env['ruc.caja.detalle.egreso'].search([('transferencia_id','=',self.id)])
                if caja_detalle_egreso:
                    caja_detalle_egreso.unlink()
            if self.check_id:
                for move in self.check_id.mapped('deposit_account_move_id'):

                    move.button_cancel()
                    move.unlink(check_move_validity=False)

                for cheque in self.check_id:
                    cheque.write({'state':'draft'})

            for move in self.move_id:


                for lineas in move.line_ids:
                    lineas.remove_move_reconcile()
                move.button_cancel()
                move.with_context(check_move_validity=False).unlink()
                    # cheq.unlink()
            self.state = 'anulado'

        else:
            raise ValidationError('No puede anular un aporte que no esta en estado confirmado')


    def pasar_borrador(self):
        if self.state == 'anulado':
            self.state = 'borrador'

        else:
            raise ValidationError('No puede pasar a borrador un aporte que no este en estado anulado')


    def confirmar(self):
        tipo_caja_chica='' #Esta variable la utilizaremos para identificar si es un registro de ingreso o egreso
        if self.cuenta_origen.caja_chica:
            tipo_caja_chica='egreso'
            self.verificar_caja_chica(self.cuenta_origen, tipo_caja_chica)
        if self.check_id:
            if self.check_id.amount > self.monto:
                raise ValidationError('El monto del cheque no puede ser mayor al monto a transferir')
            if self.check_id.amount == 0:
                raise ValidationError('El cheque no puede tener valor 0')
        dif_cambio = 0
        suma= 0
        monto_linea_debe = 0
        monto_linea_haber = 0
        dif_cambio_ex = 0
        self.diferencia_cambio = dif_cambio
        _logger.info('asaniu1')
        if self.currency_id:
            _logger.info('asaniu2')
            # if self.cuenta_origen.currency_id.id==3 and (self.cuenta_destino.currency_id.id !=3 or not self.cuenta_origen.currency_id) :
            if self.currency_id != self.currency_dest_id :
                _logger.info('asaniu3')
                if self.tasa_cambio > 0 :

                    if self.currency_id != self.env.company.currency_id:
                        suma = round(self.monto * self.tasa_cambio)
                        if self.crear_diferencia_cambio:
                            rate_origen = self.env['res.currency.rate'].search(
                                [('currency_id', '=', self.currency_id.id), ('name', '=', self.fecha)])
                            cot_origen = rate_origen.set_venta
                            if self.currency_dest_id != self.env.company.currency_id:
                                amount = round(self.currency_dest_id.with_context(date=self.fecha)._convert(suma,
                                                                                                           self.env.company.currency_id))
                                dif_cambio +=  amount - (cot_origen * self.monto)
                            else:
                                dif_cambio += suma - (cot_origen * self.monto)

                    elif self.currency_dest_id != self.env.company.currency_id:

                        suma = round(self.monto / self.tasa_cambio,2)
                        if self.crear_diferencia_cambio:

                            rate_destino = self.env['res.currency.rate'].search(
                                [('currency_id', '=', self.currency_dest_id.id), ('name', '=', self.fecha)])
                            cot_destino = rate_destino.set_venta
                            dif_cambio_ex += suma - ( self.monto / cot_destino )
                            dif_cambio += dif_cambio_ex * cot_destino


                    self.diferencia_cambio = round(dif_cambio)


                else:
                    ValidationError ('Si va a realizar una transferencia entre cuentas de Diferentes monedas debe cargar la tasa de cambio')
            # elif self.cuenta_destino.currency_id.id ==3 and (self.cuenta_origen.currency_id.id !=3 or not self.cuenta_origen.currency_id) :
            elif self.currency_id != self.env.company.currency_id :
                suma = self.monto
                # if self.tasa_cambio > 0 :
                #     suma = self.monto * self.tasa_cambio
                # else:
                #     ValidationError ('Si va a realizar una transferencia entre cuentas de Diferentes monedas debe cargar la tasa de cambio')
            else:
                suma = self.monto
        else:
            suma= self.monto
        # moneda = self.currency_id




        if suma > 0:
            vals = self.get_vals(suma, self.fecha)

            # extraemos los vals
            move_vals = vals.get('move_vals', {})
            debit_line_vals = vals.get('debit_line_vals', {})
            credit_line_vals = vals.get('credit_line_vals', {})
            dif_cambio_line_vals = vals.get('dif_cambio_line_vals', {})



            # check_move_field = vals.get('check_move_field')
            signal = vals.get('signal')
            # move_vals['ref'] = self.name

            move = self.env['account.move'].with_context({}).create(move_vals)
            debit_line_vals['move_id'] = move.id
            credit_line_vals['move_id'] = move.id

            move.line_ids.with_context(check_move_validity=False).create(debit_line_vals)
            move.line_ids.with_context(check_move_validity=False).create(credit_line_vals)
            if dif_cambio_line_vals:
                dif_cambio_line_vals['move_id'] = move.id
                move.line_ids.with_context(check_move_validity=False).create(dif_cambio_line_vals)

            print('aeeee')
            print('aeeee')
            # raise ValidationError('ss %s' % move)
            # check.write({check_move_field: move.id})
            # check.action_deposit();
            move.action_post()
            self.move_id = move
            for cheque in self.check_id:
                cheque.write({'debit_account_move_id': move.id, 'state': 'handed'})
                #cheque.message_post(_(
                #    'Ha sido debitada segun transferencia Nro. <a href=# data-oe-model=transferencias.entre.cuentas data-oe-id=%d>%s</a> .') % (
                #                    self.id, self.name))

        self.state = 'confirmado'

    
    def get_vals(self, suma, date):

        # vou_journal = check.voucher_id.journal_id

        # if self.action_type == 'deposit':
        ref = 'Trf. ' + str(self.name) + str(self.observacion)
        # check_move_field = 'deposit_account_move_id'
        journal = self.cuenta_origen
        if self.transitoria_destino:
            if not self.cuenta_origen.suspense_account_id:
                raise ValidationError('Diario Origen no posee cuenta transitoria. Favor colocarla.')

            debit_account_id = self.cuenta_destino.suspense_account_id.id
        else:
            debit_account_id = self.cuenta_destino.default_account_id.id
        if self.transitoria_origen:
            if not self.cuenta_origen.suspense_account_id:
                raise ValidationError('Diario Destino no posee cuenta transitoria. Favor colocarla.')
            credit_account_id = self.cuenta_origen.suspense_account_id.id
        else:
            credit_account_id = self.cuenta_origen.default_account_id.id

        signal = 'Transferencia'
        monto_mon_ex_c=None
        monto_mon_ex_d=None
        monto_mon_ex = None
        moneda_c = None
        moneda_d = None

        moneda_d = None
        moneda_c = None

        if (self.currency_id != self.env.company.currency_id) or (self.currency_dest_id != self.env.company.currency_id):

                if self.currency_id == self.currency_dest_id:
                    monto_mon_ex_c = -1 * self.monto
                    monto_mon_ex_d = self.monto
                    amount = round(self.currency_id.with_context(date=self.fecha)._convert(suma, self.env.company.currency_id))
                    suma = amount



                elif self.currency_id != self.currency_dest_id:

                    if self.currency_dest_id != self.env.company.currency_id:
                        if self.currency_id != self.env.company.currency_id:
                            amount = self.currency_id._convert(self.monto, self.currency_dest_id, date=self.fecha)
                        else:
                            _logger.warning('suma es %s', suma)
                            # amount = suma * self.tasa_cambio
                            amount = self.currency_dest_id._convert(suma, self.currency_id, date=self.fecha)
                            _logger.warning('amount convertido %s', amount)
                        monto_mon_ex_d = suma # * rate
                        print('a')
                        print('%s' % amount)
                        suma= amount

                    else:
                        monto_mon_ex_d = None
                        print('b')
                    if self.currency_id != self.env.company.currency_id:
                        if not monto_mon_ex_d:
                            amount = self.currency_id._convert(self.monto, self.currency_dest_id, date=self.fecha)
                            suma = amount
                        monto_mon_ex_c= -1 * self.monto

                    else:
                        _logger.warning('monto monexd %s', monto_mon_ex_d)
                        if not monto_mon_ex_d:
                            amount = self.currency_id._convert(self.suma, self.currency_dest_id, date=self.fecha)

                            suma = amount
                        monto_mon_ex_c = None
                        print('d')
                moneda_d = self.currency_dest_id.id
                moneda_c = self.currency_id.id



        debito = suma
        _logger.warning('debit %s', debito)
        credito = suma
        _logger.warning('credit %s', credito)
        name = 'Trf. ' + str(self.name)

        # ref += check.name
        move_vals = {
            'name': name,
            'journal_id': journal.id,
            'date': date,
            'ref': ref,
        }
        dif_cambio_line_vals = None
        if self.crear_diferencia_cambio:
            if self.diferencia_cambio < 0:
                if monto_mon_ex_c:
                    debito = suma - abs(self.diferencia_cambio)
                elif monto_mon_ex_d:
                    credito = suma + abs(self.diferencia_cambio)

                dif_cambio_line_vals = {
                    'name': name + ' '  + str(self.observacion),
                    'account_id': self.exchange_account_id.id,
                    'partner_id': None,
                    'debit': round(abs(self.diferencia_cambio)),
                    'currency_id': moneda_c or self.env.company.currency_id.id,
                    # 'amount_currency': -self.diferencia_cambio,
                    'credit': 0,
                    'ref': self.observacion,
                }
            elif self.diferencia_cambio > 0:
                _logger.warning('monto c %s', monto_mon_ex_c)
                _logger.warning('monto d %s', monto_mon_ex_d)

                if monto_mon_ex_c:
                    debito = suma + abs(self.diferencia_cambio)
                elif monto_mon_ex_d:
                    credito = suma - abs(self.diferencia_cambio)

                dif_cambio_line_vals = {
                    'name': name + ' ' + str(self.observacion),
                    'account_id': self.exchange_account_id.id,
                    'partner_id': None,
                    'credit': round(abs(self.diferencia_cambio)),
                    'currency_id': moneda_c or self.env.company.currency_id.id,
                    # 'amount_currency': -self.diferencia_cambio,
                    'debit': 0,
                    'ref': self.observacion,
                }

        # if not monto_mon_ex:
        #     monto_mon_ex = 0
        if not monto_mon_ex_d:
            monto_mon_ex_d = round(debito)
            _logger.warning('rounded d %s', monto_mon_ex_d)
        debit_line_vals = {
            'name': name + ' ' + str(self.observacion),
            'account_id': debit_account_id,
            'partner_id': None,
            'debit': round(debito),
            'currency_id': moneda_d or self.env.company.currency_id.id,
            'amount_currency': monto_mon_ex_d or round(debito),
            'credit': 0,
            'ref': self.observacion,
        }
        # if monto_mon_ex_c:
        #    monto_mon_ex_c = - monto_mon_ex_c
        # raise exceptions.ValidationError(debit_line_vals['ref'])

        credit_line_vals = {
            'name': name + ' ' + str(self.observacion),
            'account_id': credit_account_id,
            'partner_id': None,
            'currency_id': moneda_c or self.env.company.currency_id.id,
            'amount_currency': monto_mon_ex_c or -1 * round(credito),
            'debit': 0,
            'credit': round(credito),
            'ref': self.observacion,
        }
        # raise exceptions.ValidationError(credit_line_vals['amount_currency'])

        _logger.warning('move vals es %s', move_vals)
        _logger.warning('debit vals es %s', debit_line_vals)
        _logger.warning('credit vals es %s', credit_line_vals)
        _logger.warning('dif cambio vals es%s', dif_cambio_line_vals)
        
        return {
            'move_vals': move_vals,
            'debit_line_vals': debit_line_vals,
            'credit_line_vals': credit_line_vals,
            'dif_cambio_line_vals': dif_cambio_line_vals,
            'signal': signal,
        }
    # def crear_lineas_movimientos(self):
    #     movimientos_obj = self.env['ruc.caja.detalle.egreso']
    #     lineas_movimientos = []
    #     for transferencia in self.search([('state', '=', 'confirmado')]):
    #         linea_movimiento = movimientos_obj.create({
    #             'transferencia_id': transferencia.id,
    #             'name': transferencia.name,
    #             'fecha': transferencia.fecha,
    #
    #         })
    #         lineas_movimientos.append(linea_movimiento.id)
    #     self.write({'lineas_movimientos_ids': [(6, 0, lineas_movimientos)]})
    def verificar_caja_chica(self , diario, tipo):
        for rec in self:

                diario_utilizado = self.env['ruc.cajas'].search([['state', '=',  'abierto'], ['diario_caja', '=', diario.id]])
                if not diario_utilizado:
                    raise ValidationError('Este diario está seleccionado como Fondo Fijo, por lo que necesita una Caja abierta para poder utilizarlo. Abra una caja o utilice otro diario para realizar la transferencia')
                if diario_utilizado.usuario:
                    if diario_utilizado.usuario != self.env.user:
                        raise ValidationError('Solo el usuario %s, responsable de la caja puede pagar con este diario. ' % diario_utilizado.usuario.name )
                if tipo == 'egreso' and diario_utilizado:
                    movi_obj = self.env['ruc.caja.detalle.egreso']
                    caja = diario_utilizado.id
                    movi_vals = {
                        'caja_id': caja,
                        'name': 'Egreso por transferencia '+rec.name,
                        'fecha': rec.fecha,
                        'currency_id': rec.currency_id.id,
                        'monto': rec.monto,
                        'transferencia_id':rec.id,
                        'total': rec.monto,
                    }
                    movi_obj.create(movi_vals)
