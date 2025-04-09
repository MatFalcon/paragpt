# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError


class diferencia_recibo(models.TransientModel):

    _name = 'diferencia.recibo'


    recibo = fields.Many2one('account.recibo',string="Recibo")

    diferencia = fields.Selection([('utilidad','Utilidad'),('a_cuenta','A Favor del Cliente/Anticipo'),('cambio','Diferencia de Cambio')],default='a_cuenta',string="Guardar Diferencia Como:")
    journal_id = fields.Many2one('account.journal','Diario diferencia de cambio')
    account_id = fields.Many2one('account.account','Cuenta Contable',default=lambda self: self._get_default_account())
    monto = fields.Monetary(string="Monto")

    currency_id = fields.Many2one('res.currency',string="Moneda")

    def _get_default_account(self):
        for rec in self:
            if self.env.company.cuenta_utilidad_recibo:
                return self.env.company.cuenta_utilidad_recibo
            else:
                return None

    @api.onchange('diferencia')
    def set_journal_diferencia(self):
        for rec in self:
            if rec.diferencia == 'cambio':
                journal = self.env['account.journal'].search([('name', '=', 'Diferencia de cambio'),('company_id','=',self.env.company.id)])
                if len(journal) > 0:
                    rec.journal_id = journal[0]
                    if rec.recibo.diferencia_cambio > 0:
                        rec.account_id = journal.default_credit_account_id
                    else:
                        rec.account_id = journal.default_debit_account_id



    def procesar(self):
        if self.diferencia:
            self.recibo.diferencia=self.diferencia
            if self.diferencia == 'utilidad':
                if not self.account_id:
                    raise ValidationError('No se encuentra asignada cuenta de utilidad en recibo. Debe configurarla en los datos de la compañia. Verifique con Administrador')
                self.recibo.with_context(cuenta_utilidad=self.account_id,monto_utilidad=self.monto).set_confirmado()
            elif self.diferencia == 'cambio':
                if self.recibo.diferencia_cambio == 0:
                    raise ValidationError('No existe diferencia de cambio a aplicar')
                else:
                    self.recibo.diario_diferencia = self.journal_id
                    self.recibo.cuenta_diferencia = self.account_id
                    self.recibo.set_confirmado()
            else:
                if not self.recibo.pagos_facturas_ids:
                    self.recibo.with_context(tipo='a_favor').set_confirmado()
                else:
                    self.recibo.set_confirmado()



        else:
            raise ValidationError ('Debe seleccionar a donde ira la diferencia')



