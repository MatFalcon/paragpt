# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from xlrd import open_workbook
import base64
from datetime import date, datetime, timedelta
import xlrd


class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'

    nombre_xlsx = fields.Char(string="Nombre del Archivo", copy=False)
    archivo_xlsx = fields.Binary(string="Planilla Excel", copy=False)

    def get_first_date_of_month(self, year, month):
        first_date = datetime(year, month, 1)
        return first_date.strftime("%Y-%m-%d")

    def get_last_date_of_month(self, year, month):
        if month == 12:
            last_date = datetime(year, month, 31)
        else:
            last_date = datetime(year, month + 1, 1) + timedelta(days=-1)
        return last_date.strftime("%Y-%m-%d")

    @api.model
    def make_float(self,num):
        num = num.replace(' ', '').replace("-", "")
        return float(num)

    def cargar_lineas(self):
        if self.archivo_xlsx:
            year = self.date_from.year
            # att = self.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=', 23146)])
            file_candidate = base64.b64decode(self.archivo_xlsx)
            file = "/tmp/" + self.name + "_" + str(datetime.today().strftime('%Y-%m-%d')) + ".xlsx"
            file_final = open(file, 'wb')
            file_final.write(file_candidate)
            file_final.close()
            workbook = xlrd.open_workbook(file)
            sheet = workbook.sheet_by_index(0)
            final_archivo = sheet.nrows
            for r in range(3,sheet.nrows):
                if sheet.cell_value(r,0) == '' and sheet.cell_value(r,1) == '':
                    final_archivo = int(r)
            if final_archivo:
                #line_ids = []
                for x in range(3,final_archivo):
                    cod_cuenta = str(sheet.cell_value(x, 0))
                    cod_cuenta = cod_cuenta.replace('.0','')
                    cod_cuenta_analitica = str(sheet.cell_value(x, 1))
                    meses = {
                        '1': sheet.cell_value(x, 3),
                        '2': sheet.cell_value(x, 4),
                        '3': sheet.cell_value(x, 5),
                        '4': sheet.cell_value(x, 6),
                        '5': sheet.cell_value(x, 7),
                        '6': sheet.cell_value(x, 8),
                        '7': sheet.cell_value(x, 9),
                        '8': sheet.cell_value(x, 10),
                        '9': sheet.cell_value(x, 11),
                        '10': sheet.cell_value(x, 12),
                        '11': sheet.cell_value(x, 13),
                        '12': sheet.cell_value(x, 14),
                    }
                    analytic_account_id = self.env['account.analytic.account'].search([('name','=',cod_cuenta_analitica)])
                    account_id = self.env['account.account'].search([('code','=',cod_cuenta)])
                    if account_id and analytic_account_id:
                        general_budget_id = self.env['account.budget.post'].search([('account_ids','=',account_id.id)])
                        if not general_budget_id:
                            vals = {
                                'company_id': self.env.user.company_id.id,
                                'name': account_id.name,
                                'account_ids': [(6, 0, account_id.ids)]
                            }
                            general_budget_id = self.env['account.budget.post'].create(vals)
                        if general_budget_id:
                            for key, value in meses.items():
                                line_anterior = self.env['crossovered.budget.lines'].search([('general_budget_id','=', general_budget_id[0].id),
                                                                                             ('analytic_account_id','=', analytic_account_id.id),
                                                                                             ('crossovered_budget_id','=', self.id),
                                                                                             ('date_from','=', self.get_first_date_of_month(year, int(key))),
                                                                                             ('date_to','=', self.get_last_date_of_month(year, int(key)))
                                                                                             ])
                                if line_anterior:
                                    line_anterior.unlink()
                                self.write({'crossovered_budget_line':
                                                [(0, 0, {
                                                    'general_budget_id': general_budget_id[0].id,
                                                    'date_from': self.get_first_date_of_month(year,int(key)),
                                                    'date_to': self.get_last_date_of_month(year,int(key)),
                                                    'analytic_account_id': analytic_account_id.id if analytic_account_id else False,
                                                    'planned_amount': value if not isinstance(value, str) else 0
                                                })]
                                            })
        else:
            raise exceptions.ValidationError('Por favor, suba un archivo ')
