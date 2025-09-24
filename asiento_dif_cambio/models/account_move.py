from ast import literal_eval

from odoo import models, exceptions,fields, api
import datetime
import calendar


class AccountMove(models.Model):
    _inherit = 'account.move'

    asiento_automatico = fields.Boolean(string="Asiento por diferencia de cambio automatico", default=False, copy=False)

    @api.model
    def revertir_asiento_dif_auto(self):
        date = datetime.date.today()
        journal_id = self.env['ir.config_parameter'].sudo().get_param('journal_dif_id')
        if not journal_id:
            raise exceptions.UserError("Debe definir un diario de diferencia de cambio")
        asiento_fecha = self.env['account.move'].search([('journal_id', '=', int(journal_id)),
                                                         ('asiento_automatico', '=', True),
                                                         ('date', '<=', date),
                                                         ('state', '=', 'posted'),
                                                         ('reversal_move_id', '=', False),
                                                         ('reversed_entry_id','=',False)])
        if asiento_fecha:
            for afa in asiento_fecha:
                afa.revertirAsiento(date=date,journal_id=int(journal_id))
            self.env['ir.config_parameter'].set_param('last_rate_compra', '')
            self.env['ir.config_parameter'].set_param('last_rate_venta', '')
        return

    def revertirAsiento(self,date,journal_id):
        vals = {
            'date': date,
            'journal_id': journal_id,
            'ref': 'Reversión de ' + self.name,
            'currency_rate': self.currency_rate,
            'asiento_automatico': True,
            'reversed_entry_id': self.id
        }
        move_id = self.env['account.move'].create(vals)
        self.write({'reversal_move_id': [(4, move_id.id)]})
        line_ids = []
        for l in self.line_ids:
            line_ids.append((0, 0, {
                'account_id': l.account_id.id,
                'move_id': move_id.id,
                'currency_id': l.currency_id.id,
                'amount_currency': l.amount_currency,
                'debit': l.credit if l.credit else 0,
                'credit': l.debit if l.debit else 0
            }))
        move_id.write({'line_ids': line_ids})
        move_id.action_post()

    def create_asiento_dif_auto(self):
        date = datetime.date.today()
        rate = self.env['res.currency.rate'].search([('name', '=', date)])
        if rate:
            rate_compra = rate.inverse_company_rate_tipo_cambio_comprador
            rate_venta = rate.inverse_company_rate
            last_rate_compra = self.env['ir.config_parameter'].get_param('last_rate_compra') != str(rate_compra)
            last_rate_venta = self.env['ir.config_parameter'].get_param('last_rate_venta') != str(rate_venta)
            if last_rate_venta or last_rate_compra:
                self.env['account.move'].create_asiento_dif()

    @api.model
    def create_asiento_dif(self):
        date = datetime.date.today()
        journal_id = self.env['ir.config_parameter'].sudo().get_param('journal_dif_id')
        if not journal_id:
            raise exceptions.UserError("Debe definir un diario de diferencia de cambio")
        asiento_fecha = self.env['account.move'].search([('journal_id', '=', int(journal_id)),
                                                         ('asiento_automatico', '=', True),
                                                         ('date', '<=', date),
                                                         ('state','=','posted'),
                                                         ('reversal_move_id','=',False),
                                                         ('reversed_entry_id','=',False)])
        if asiento_fecha:
            for a in asiento_fecha:
                a.revertirAsiento(date=date,journal_id=int(journal_id))

        rate = self.env['res.currency.rate'].search([('name', '=', date)])
        if rate:
            rate_compra = rate.inverse_company_rate_tipo_cambio_comprador
            rate_venta = rate.inverse_company_rate
            self.env['ir.config_parameter'].set_param('last_rate_compra', rate_compra)
            self.env['ir.config_parameter'].set_param('last_rate_venta', rate_venta)
            asiento = {
                'date': date,
                'journal_id': int(journal_id),
                'ref': 'Asiento por diferencia de cambio (Cuentas Activas)',
                'currency_rate': rate_compra,
                'asiento_automatico':True
            }
            move_id = self.env['account.move'].create(asiento)
            asiento = {
                'date': date,
                'journal_id': int(journal_id),
                'ref': 'Asiento por diferencia de cambio (Cuentas Pasivas)',
                'currency_rate': rate_compra,
                'asiento_automatico':True
            }
            move_id_2 = self.env['account.move'].create(asiento)

            move_id.create_asiento_mas(date)
            move_id_2.create_asiento_menos(date)
        return

    def create_asiento_mas(self, fecha_fin):
        user_type_ids = literal_eval(
            self.env['ir.config_parameter'].sudo().get_param('asiento_dif_cambio.cuenta_ganancia_ids'))

        amls = self.env['account.move.line'].search(
            [('parent_state', '=', 'posted'), ('account_id.currency_id.name', '=', 'USD'),
             ('date', '<=', fecha_fin), ('account_id.id', 'in', user_type_ids)])

        account_ids = list(set(amls.mapped('account_id')))
        total = 0
        total_dif = 0
        line_ids = []
        dif_credit = 0
        dif_debit = 0
        for i in account_ids:
            i.total_divisas = sum(amls.filtered(lambda x:x.account_id.id == i.id).mapped('amount_currency'))
            i.total_debe = sum(amls.filtered(lambda x:x.account_id.id == i.id and x.debit > 0).mapped('debit'))
            i.total_haber = sum(amls.filtered(lambda x:x.account_id.id == i.id and x.credit > 0).mapped('credit'))

            i.saldo = i.total_debe - i.total_haber
            i.total_divisas = i.total_divisas * self.currency_rate

            diferencia = round(i.total_divisas - i.saldo)
            total += diferencia
            if diferencia > 0:
                line_ids.append((0, 0, {
                    'account_id': i.id,
                    'move_id': self.id,
                    'currency_id': i.currency_id.id,
                    'amount_currency': 0,
                    'debit': diferencia if diferencia > 0 else (-1 * diferencia),
                }))
                dif_debit = dif_debit + diferencia
            elif diferencia < 0:
                line_ids.append((0, 0, {
                    'account_id': i.id,
                    'move_id': self.id,
                    'currency_id': i.currency_id.id,
                    'amount_currency': 0,
                    'credit': diferencia if diferencia > 0 else (-1 * diferencia),
                }))
                dif_credit = dif_credit + diferencia

            total_dif += diferencia if diferencia > 0 else (-1 * diferencia)

        dif_debit = round(dif_debit)
        dif_credit = round(dif_credit)
        account_id = self.env['ir.config_parameter'].sudo().get_param('cuenta_ganancia_dif_id')
        if not account_id:
            raise exceptions.UserError("Debe definir una cuenta para ganancias por diferencia de cambio")
        line_ids.append((0, 0, {
            'account_id': int(account_id),
            'move_id': self.id,
            'currency_id': self.env['res.currency'].search([('name', '=', 'PYG')]).id,
            'amount_currency': -1 * dif_debit,
            'credit': dif_debit if dif_debit > 0 else (-1 * dif_debit),
        }))
        account_id = self.env['ir.config_parameter'].sudo().get_param('cuenta_perdida_dif_id')
        if not account_id:
            raise exceptions.UserError("Debe definir una cuenta para perdidas por diferencia de cambio")
        line_ids.append((0, 0, {
            'account_id': int(account_id),
            'move_id': self.id,
            'currency_id': self.env['res.currency'].search([('name', '=', 'PYG')]).id,
            'amount_currency': -1 * dif_credit,
            'debit': dif_credit if dif_credit > 0 else (-1 * dif_credit),
        }))
        self.write({'line_ids': line_ids})
        if total_dif == 0:
            self.unlink()
        else:
            self.action_post()

    def create_asiento_menos(self, fecha_fin):
        user_type_ids = literal_eval(
            self.env['ir.config_parameter'].sudo().get_param('asiento_dif_cambio.cuenta_perdida_ids'))

        amls = self.env['account.move.line'].search(
            [('parent_state', '=', 'posted'), ('account_id.currency_id.name', '=', 'USD'),
             ('date', '<=', fecha_fin), ('account_id.id', 'in', user_type_ids)])

        account_ids = list(set(amls.mapped('account_id')))
        total = 0
        total_dif = 0
        line_ids = []
        dif_credit = 0
        dif_debit = 0
        for i in account_ids:
            total_debe = 0
            total_haber = 0
            for am in amls.filtered(lambda x: x.account_id.id == i.id):
                total_debe += am.debit
                total_haber += am.credit
            total_divisas = sum(amls.filtered(lambda x: x.account_id.id == i.id).mapped('amount_currency'))
            i.total_debe = sum(
                amls.filtered(lambda x: x.account_id.id == i.id).mapped('debit'))
            i.total_haber = sum(
                amls.filtered(lambda x: x.account_id.id == i.id).mapped('credit'))
            print(i.total_debe)
            print(i.total_haber)

            i.saldo = i.total_debe - i.total_haber
            i.total_divisas = total_divisas * self.currency_rate

            diferencia = round(i.total_divisas - i.saldo)
            total += diferencia
            if diferencia > 0:
                line_ids.append((0, 0, {
                    'account_id': i.id,
                    'move_id': self.id,
                    'currency_id': i.currency_id.id,
                    'amount_currency': 0,
                    'debit': diferencia if diferencia > 0 else (-1 * diferencia),
                }))
                dif_debit = dif_debit + diferencia
            elif diferencia < 0:
                line_ids.append((0, 0, {
                    'account_id': i.id,
                    'move_id': self.id,
                    'currency_id': i.currency_id.id,
                    'amount_currency': 0,
                    'credit': diferencia if diferencia > 0 else (-1 * diferencia),
                }))
                dif_credit = dif_credit + diferencia

            total_dif += diferencia if diferencia > 0 else (-1 * diferencia)

        dif_debit = round(dif_debit)
        dif_credit = round(dif_credit)
        account_id = self.env['ir.config_parameter'].sudo().get_param('cuenta_ganancia_dif_id')
        if not account_id:
            raise exceptions.UserError("Debe definir una cuenta para ganancias por diferencia de cambio")
        if dif_debit:
            line_ids.append((0, 0, {
                'account_id': int(account_id),
                'move_id': self.id,
                'currency_id': self.env['res.currency'].search([('name', '=', 'PYG')]).id,
                'amount_currency': -1 * dif_debit,
                'credit': dif_debit if dif_debit > 0 else (-1 * dif_debit),
            }))
        account_id = self.env['ir.config_parameter'].sudo().get_param('cuenta_perdida_dif_id')
        if not account_id:
            raise exceptions.UserError("Debe definir una cuenta para perdidas por diferencia de cambio")
        if dif_credit:
            line_ids.append((0, 0, {
                'account_id': int(account_id),
                'move_id': self.id,
                'currency_id': self.env['res.currency'].search([('name', '=', 'PYG')]).id,
                'amount_currency': -1 * dif_credit,
                'debit': dif_credit if dif_credit > 0 else (-1 * dif_credit),
            }))
        self.write({'line_ids': line_ids})
        if total_dif == 0:
            self.unlink()
        else:
            self.action_post()