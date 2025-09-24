# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError
from xlrd import open_workbook
import base64
from datetime import datetime
import xlrd
import locale

locale.setlocale(locale.LC_ALL, '')


class ImportacionExtracto(models.Model):
    _name = 'importacion_extracto'

    name = fields.Char('Nombre')
    file = fields.Binary('Archivo', readonly=True)


class AccountBankStatement(models.Model):
    _inherit = 'account.bank.statement'

    nombre_xlsx = fields.Char(string="Nombre del Archivo", copy=False)
    archivo_xlsx = fields.Binary(string="Planilla Excel", copy=False)

    def convertir_fecha(self, fecha, linea):
        if type(fecha) in [int, float]:
            excel_date = int(fecha)
            dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + excel_date - 2)
            return dt
        if type(fecha) in [str]:
            try:
                dt = datetime.strptime(fecha, '%d/%m/%Y')
                if dt:
                    return dt
            except ValueError:
                print(
                    "Este es el formato de texto de fecha incorrecto. Debe ser dia/mes/año. Verifique si no hay ningun espacio en blanco.")
        else:
            raise exceptions.ValidationError(
                'La fecha debe cargarse correctamente, por favor verifique la linea ' + str(linea))

    @api.model
    def make_float(self, num):
        num = num.replace(' ', '').replace("-", "")
        return float(num)

    def cargar_lineas(self):
        if self.archivo_xlsx:
            # att = self.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=', 23146)])
            file_candidate = base64.b64decode(self.archivo_xlsx)
            file = "/tmp/" + self.name + "_" + str(datetime.today().strftime('%Y-%m-%d')) + ".xlsx"
            file_final = open(file, 'wb')
            file_final.write(file_candidate)
            file_final.close()
            workbook = xlrd.open_workbook(file)
            sheet = workbook.sheet_by_index(0)
            final_archivo = False
            for r in range(9, sheet.nrows):
                if sheet.cell_value(r, 0) == '' and sheet.cell_value(r, 1) == '' and sheet.cell_value(r, 2) == '':
                    final_archivo = int(r)
            if final_archivo:
                line_ids = []
                for x in range(9, final_archivo):
                    if sheet.cell_value(x, 3) != '' and sheet.cell_value(x, 4) != '' and sheet.cell_value(x, 5) != '':
                        date = self.convertir_fecha(sheet.cell_value(x, 0), x)
                        ref_number = str(sheet.cell_value(x, 2))
                        ref_number = ref_number.replace('.0', '')
                        payment_ref = str(sheet.cell_value(x, 1)) + ' ' + ref_number
                        debit = sheet.cell_value(x, 3)
                        credit = sheet.cell_value(x, 4)
                        if type(credit) not in [int, float]:
                            try:
                                credit = locale.atof(credit)
                            except ValueError:
                                credit = credit.replace('.', '')
                            credit = float(credit)
                        if type(debit) not in [int, float]:
                            try:
                                debit = locale.atof(debit)
                            except ValueError:
                                debit = debit.replace('.', '')
                            debit = float(debit)
                        if date and payment_ref and (credit or debit):
                            statement_line_existente = self.env['account.bank.statement.line'].search(
                                [('payment_ref', '=', payment_ref)])
                            if not statement_line_existente:
                                line_ids.append((0, 0, {
                                    'date': date,
                                    'amount': credit if credit > 0 else debit * -1,
                                    'payment_ref': payment_ref
                                }))
                self.write({'line_ids': line_ids})
        else:
            raise exceptions.ValidationError('Por favor, suba un archivo ')
