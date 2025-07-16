# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError


class movimientos_caja(models.Model):
    _inherit = "ruc.caja.detalle"
    recibo_id = fields.Many2one('account.recibo')
    total_recibo = fields.Float(string='Total', compute="_total_recibo")
    total_banco = fields.Float(string="Total banco", compute='_total_banco',store=True)
    cobro_cheque_visual = fields.Float()
    currency_id = fields.Many2one(related='recibo_id.currency_id', readonly=True)


    @api.depends('recibo_id.payment_ids')
    def _total_banco(self):
        for rec in self:
            payments = rec.recibo_id.payment_ids.filtered(lambda x: x.journal_id.type == 'bank')
            if len(payments) > 0:
                rec.total_banco = sum(payments.mapped('amount'))
    
    def _calcular_ingresos_ex(self):
        total_in = 0
        total_eg = 0
        for ingre in self:
            total_in = 0
            total_eg = 0
            if ingre.movimientos_ids:

                for movi in ingre.movimientos_ids:
                    if movi.tipo == 'ingreso':
                        total_in = total_in + movi.total_recibo
                    # if movi.tipo == 'egreso' and  ingre.currency_id != movi.currency_id :
                    #     total_eg = total_eg + movi.total
            else:
                total_in = 0

            ingre.total_ingreso_mon_ex = total_in
            ingre.total_cobrado = total_in


    def _total_recibo(self):
        self.total_recibo = self.recibo_id.total_cobros

    def agregar_punto_de_miles(self, numero):
        numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(numero))), 3)])[::-1]
        return numero_con_punto


class Ruc_Cajas_Elektron(models.Model):
    _inherit = "ruc.cajas"


    def lista_cobros(self):
        ruc_detalles = self.movimientos_ids.sorted(key=lambda r:r.recibo_id.fecha)
        cobros=[]
        for r in ruc_detalles:
            if r.recibo_id.currency_id:
                if r.recibo_id.currency_id == self.env.company.currency_id:
                    for c in r.recibo_id.payment_ids:
                        cobros.append(c)
        return cobros

    def lista_cobros_usd(self):
        ruc_detalles = self.movimientos_ids.sorted(key=lambda r:r.recibo_id.fecha)
        cobros=[]
        for r in ruc_detalles:
            if r.recibo_id.currency_id:
                if r.recibo_id.currency_id != self.env.company.currency_id:
                    for c in r.recibo_id.payment_ids:
                        cobros.append(c)
        return cobros

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

