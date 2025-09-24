from odoo import api, exceptions, fields, models
import base64
from datetime import datetime
import xlrd


class WizardCuentasBancarias(models.TransientModel):
    _name = 'wizard_cuentas_bancarias'
    _description = 'Wizard cuentas bancarias'

    nombre_xlsx = fields.Char(string="Nombre del Archivo", copy=False)
    archivo_xlsx = fields.Binary(string="Planilla Excel", copy=False)

    def cargar_lineas(self):
        if self.archivo_xlsx:
            # att = self.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=', 23146)])
            file_candidate = base64.b64decode(self.archivo_xlsx)
            file = "/tmp/" + self.nombre_xlsx + "_" + str(datetime.today().strftime('%Y-%m-%d')) + ".xlsx"
            file_final = open(file, 'wb')
            file_final.write(file_candidate)
            file_final.close()
            workbook = xlrd.open_workbook(file)
            sheet = workbook.sheet_by_index(0)
            final_archivo = sheet.nrows
            if final_archivo:
                for x in range(2, final_archivo):
                    banco = str(sheet.cell_value(x, 1))
                    bank_id = self.env['res.bank'].search([('name','=',banco)])
                    if not bank_id:
                        bank_id = self.env['res.bank'].create({
                            'name': banco
                        })
                    moneda = str(sheet.cell_value(x, 2))
                    if 'guarani' in moneda.lower():
                        currency_id = self.env['res.currency'].search([('name','=','PYG')])
                    elif 'dolar' in moneda.lower():
                        currency_id = self.env['res.currency'].search([('name','=','USD')])
                    ruc = str(sheet.cell_value(x, 3))
                    partners = self.env['res.partner'].search([('vat','=',ruc)])
                    partner_id = False
                    if len(partners) > 1:
                        max_total = 0
                        for pid in partners:
                            partner_novedades_total = len(self.env['pbp.novedades'].search([('partner_id','=',pid.id)]))
                            if partner_novedades_total > max_total:
                                partner_id = pid
                                max_total = partner_novedades_total
                        if not max_total:
                            partner_id = partners[0]
                    else:
                        partner_id = partners
                    nro_cuenta = str(sheet.cell_value(x, 4))
                    nro_cuenta = nro_cuenta.replace('.0','')
                    if 'liquidacion' in str(sheet.cell_value(x, 5)).lower():
                        cuenta_liquidaciones = True
                    else:
                        cuenta_liquidaciones = False
                    if partner_id and bank_id and nro_cuenta and currency_id:
                        vals = {
                            'bank_id':bank_id.id,
                            'cuenta_liquidaciones':cuenta_liquidaciones,
                            'acc_number': nro_cuenta,
                            'acc_holder_name': partner_id.name,
                            'partner_id':partner_id.id,
                            'currency_id': currency_id.id,
                            'ruc_ci':partner_id.vat
                        }
                        cuenta_existente = self.env['res.partner.bank'].search([('acc_number','=',nro_cuenta),('bank_id','=',bank_id.id)])
                        if cuenta_existente:
                            cuenta_existente.write(vals)
                        else:
                            self.env['res.partner.bank'].create(vals)
        else:
            raise exceptions.ValidationError('Por favor, suba un archivo ')
