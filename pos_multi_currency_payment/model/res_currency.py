# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class res_currency(models.Model):

    _inherit = 'res.currency'

    rate_venta=fields.Float(digits=(12,12),compute="obtener_rate_venta")


    def _get_rates_venta(self, company, date):
        query = """SELECT c.id,
                          COALESCE((SELECT r.rate_venta FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company.id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        return currency_rates


    @api.one
    @api.depends('rate_ids.rate_venta')
    def obtener_rate_venta(self):
        date = self._context.get('date') or fields.Date.today()
        company = self.env['res.company'].browse(self._context.get('company_id')) or self.env['res.users']._get_company()
        # the subquery selects the last rate before 'date' for the given currency/company
        currency_rates = self._get_rates_venta(company, date)
        for currency in self:
            currency.rate_venta = currency_rates.get(currency.id) or 1.0


class res_currency_rate(models.Model):

    _inherit = "res.currency.rate"

    cotizacion_venta_caja = fields.Float(string="Cotizacion de Venta en Caja")
    rate_venta = fields.Float(digits=(12,12),string="Rate de Venta",default=1)
    ambito_moneda= fields.Selection(related='currency_id.ambito',readonly=True)

    @api.onchange('cotizacion_venta_caja')
    def obtener_rate(self):
            if self.cotizacion_venta_caja>0:
                self.rate_venta= 1/ self.cotizacion_venta_caja

    @api.model
    def create(self, vals):
        if vals.get('rate', False) and vals.get('rate') == 0:
            raise UserError('Rate can not is 0')
        return super(res_currency_rate, self).create(vals)

    # @api.multi
    def write(self, vals):
        if vals.get('rate', False) and vals.get('rate') == 0:
            raise UserError('Rate can not is 0')
        return super(res_currency_rate, self).write(vals)
