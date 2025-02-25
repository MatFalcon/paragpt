# -*- coding: utf-8 -*-
import psycopg2
import logging

from odoo import api, fields, models, tools,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)




class PosSessionParaguay(models.Model):
    _inherit = "pos.session"

    total_gs = fields.Float()
    total_usd = fields.Float()

    def _loader_params_res_company(self):
        res = super()._loader_params_res_company()
        # if not self.config_id.is_spanish:
        # return res
        res["search_params"]["fields"] += ["account_sale_tax_id"]
        return res


    def _loader_params_res_partner(self):
        res = super()._loader_params_res_partner()
        res["search_params"]["fields"].append("ruc")
        res["search_params"]["fields"].append("rucdv")
        return res

    def ordenar_order(self):
        list_order_fac=[]
        list_order_not_fact=[]
        list_result=[]
        list_order_fac=self.order_ids.filtered(lambda r:r.state=="invoiced")
        list_order_not_fact=self.order_ids.filtered(lambda r:r.state!="invoiced")
        list_order_fac.sorted(key=lambda r:r.invoice_id.nro_factura)
        list_order_not_fact.sorted(key=lambda r:r.name)
        list_result=list_order_fac+list_order_not_fact
        return list_result


    def agregar_punto_de_miles(self,numero):
        entero=int(numero)
        decimal='{0:.2f}'.format(numero-entero)
        entero_string='.'.join([str(int(entero))[::-1][i:i+3] for i in range(0,len(str(int(entero))),3)])[::-1]
        if decimal == '0.00':
            numero_con_punto=entero_string
        else:
            decimal_string=str(decimal).split('.')
            numero_con_punto=entero_string+','+decimal_string[1]
        return numero_con_punto

    # @api.multi
    def print_report_caja(self):
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://villanflor.sati.com.py/report/pdf/pos_paraguay.caja_report/' + str(self.id),
            'target': 'new',
            'tag': 'reload',
            'res_id': self.id,
        }

    def totales_diarios(self,statement_ids):
        dic_total={}
        total_gs = 0
        total_usd = 0
        for s in statement_ids:
            diario=s.journal_id
            if diario.pos_currency_id != self.env.user.company_id.currency_id:
                suma = sum([p.amount for p in s.line_ids if p.pos_statement_id.state != 'done'])
                total_usd = total_usd + suma
            else:
                suma = sum([p.amount_pago for p in s.line_ids if p.pos_statement_id.state != 'done'])
                total_gs = total_gs + suma
            dic_total.setdefault(diario,suma)
            self.total_gs = total_gs
            self.total_usd = total_usd
        return dic_total.items()
