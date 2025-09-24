from odoo import api, fields, models
import datetime


class WizardBancoSudameris(models.TransientModel):
    _name = 'pbp.wizard_bancos_sudameris'
    _description = 'Wizard Banco Sudameris'


    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True)

    def print_wizard_bancos_sudameris_report(self):
        return self.env.ref('pbp.wizard_bancos_sudameris_report').report_action(self)

    def get_values_for_report_bancos_sudameris(self):
        def get_formatted_string_left(text, lenght, fill_character=' '):
            text = text or ''
            return text[:lenght]

        def get_formatted_string_right(text, lenght, fill_character='0'):
            text = text or ''
            return text[:lenght]

        lineas_exportar = self.env['pbp.exportar_liquidaciones'].search([
            ('fecha', '>=', self.date_from),
            ('fecha', '<=', self.date_to),
            ('currency_id','=',self.currency_id.id)
        ])

        final_text = ''

        if not lineas_exportar:
            return final_text

        c = 0
        fecha_servicio = max(lineas_exportar.mapped('fecha'))
        referencia = str(fecha_servicio.year)
        referencia += str(fecha_servicio.month).rjust(2, '0')
        referencia += str(fecha_servicio.day)[0]
        referencia += '1'
        referencia += '0'
        referencia += self.env.user.company_id.banco_sudameris_cod_contrato
        referencia = referencia[:18]
        fecha_servicio = datetime.date.strftime(fecha_servicio, '%d/%m/%y')
        moneda = '6900' if self.currency_id.name == 'PYG' else '1'

        rucs = set(lineas_exportar.mapped('nro_documento'))
        for r in rucs:
            l = lineas_exportar.filtered(lambda x:x.nro_documento == r)
            cuenta_sipap = l[0].cuenta_credito.ljust(16, '0')
            if l:
                c = c+1
                final_text += '\n'
                final_text += 'D;'
                final_text += get_formatted_string_left('Pago de Liquidaciones', 30)  # Concepto de pago
                final_text += ';'
                final_text += get_formatted_string_left(referencia, 18)  # Referencia
                final_text += ';'
                final_text += get_formatted_string_left('586', 3)  # COD Pais (Paraguay)
                final_text += ';'
                final_text += get_formatted_string_left('3', 2)  # RUC/CI
                final_text += ';'
                final_text += get_formatted_string_left(r.replace('-',''), 12)  # N. RUC/CI
                final_text += ';'
                final_text += get_formatted_string_left(l[0].titular_cuenta, 60)  # Apellido o Razon Social
                final_text += ';'
                final_text += get_formatted_string_left('', 30)  # Apelido/Nombre
                final_text += ';'
                final_text += get_formatted_string_left('', 30)  # Apelido/Nombre
                final_text += ';'
                final_text += get_formatted_string_left('', 30)  # Apelido/Nombre
                final_text += ';'
                final_text += get_formatted_string_left(moneda, 4)  # Moneda
                final_text += ';'
                final_text += get_formatted_string_left(str(sum(l.mapped('monto'))), 18)  # Importe
                final_text += ';'
                final_text += get_formatted_string_left('1', 20)  # Nro Factura
                final_text += ';'
                final_text += get_formatted_string_left(self.env.user.company_id.banco_sudameris_email_asociado, 20)  # Email Proveedor
                final_text += ';'
                final_text += get_formatted_string_left('', 20)  # Telefono
                final_text += ';'
                final_text += get_formatted_string_left('0', 3)  # Sucursal de la cuenta
                final_text += ';'
                #20 = Crédito Cta.Cte. / 21 = Crédito C.Ahorro / 62 = Transf.SIPAP
                final_text += get_formatted_string_left('20', 3)  # Modulo de la cuenta
                final_text += ';'
                final_text += get_formatted_string_left(moneda, 4)  # Moneda de la cuenta
                final_text += ';'
                final_text += get_formatted_string_left('0', 4)  # Papel de la cuenta
                final_text += ';'
                final_text += get_formatted_string_left(l[0].cuenta_credito, 9)  # Nro de Cuenta
                final_text += ';'
                final_text += get_formatted_string_left('0', 9)  # Operacion
                final_text += ';'
                final_text += get_formatted_string_left('0', 3)  # Sub-Operacion
                final_text += ';'
                final_text += get_formatted_string_left('0', 10)  # Cuenta Prepaga
                final_text += ';'
                final_text += get_formatted_string_left(cuenta_sipap, 16)  # Nro. Cuenta Sipap
                final_text += ';'
                final_text += get_formatted_string_left(l[0].codigo_banco, 20)  # Codigo de Entidad
                final_text += ';'
                final_text += get_formatted_string_left('586', 3)  # Pais del autorizado
                final_text += ';'
                final_text += get_formatted_string_left('3', 2)  # Tipo de Documento del Autorizado
                final_text += ';'
                final_text += get_formatted_string_left(r.replace('-',''), 12) # Nro de Documento del Autorizado
                final_text += ';'
                final_text += get_formatted_string_left('', 100)  # Continuacion nro Factura
                final_text += ';'
                #20= Crédito Cta. Cte. / 21= Crédito C.Ahorro / 62= Transf. SIPAP
                final_text += get_formatted_string_left('62', 4)  # Cod. de Modalidad del Pago

        cuenta = self.env.user.company_id.banco_sudameris_nro_cuenta_pyg if self.currency_id.name == 'PYG' else self.env.user.company_id.banco_sudameris_nro_cuenta_usd

        first_line = 'H'
        first_line += ';'
        first_line += get_formatted_string_right(self.env.user.company_id.banco_sudameris_cod_contrato, 9) #Cód contrato
        first_line += ';'
        first_line += get_formatted_string_left(self.env.user.company_id.banco_sudameris_email_asociado, 50) #Email asociado
        first_line += ';'
        first_line += get_formatted_string_right(moneda, 4) #Moneda
        first_line += ';'
        first_line += get_formatted_string_right(str(c), 9) #Cantidad de Pagos
        first_line += ';'
        final_text += get_formatted_string_right(str(int(sum(lineas_exportar.mapped('monto')))), 18) #Importe total
        first_line += ';'
        first_line += get_formatted_string_left('N', 1)  # Retención del IVA
        first_line += ';'
        first_line += get_formatted_string_left(fecha_servicio, 8) #Fecha de Servicio
        first_line += ';'
        first_line += get_formatted_string_left(referencia, 18)  # REFERENCIA
        first_line += ';'
        first_line += get_formatted_string_left('1', 1)  # Debito/Credito
        first_line += ';'
        first_line += get_formatted_string_right(cuenta, 9)
        first_line += ';'
        first_line += get_formatted_string_left('10', 3)  # SUCURSAL
        first_line += ';'
        first_line += get_formatted_string_left('20', 3)  # Modulo
        first_line += ';'
        first_line += get_formatted_string_left(moneda, 4)  # Moneda
        first_line += ';'
        first_line += get_formatted_string_left('0', 4)  # Papel de la Cta.
        first_line += ';'
        first_line += get_formatted_string_left('0', 9)  # Operación de la Cta.
        first_line += ';'
        first_line += get_formatted_string_left('0', 3)  # Sub-Operación de la Cta.
        first_line += ';'
        first_line += get_formatted_string_left('0', 3)  # Tipo de Operación de la Cta.
        first_line += ';'
        first_line += get_formatted_string_right('//', 8)  # Fecha Cab 1
        first_line += ';'
        first_line += get_formatted_string_right('//', 8)  # Fecha Cab 2
        first_line += ';'
        first_line += get_formatted_string_right('0', 18)  # Importe 1
        first_line += ';'
        first_line += get_formatted_string_right('0', 18) # Importe 2

        final_text = first_line + final_text

        return final_text
