from odoo import api, fields, models
import datetime


class WizardBancoSudameris(models.TransientModel):
    _name = 'wizard_bancos_sudameris'
    _description = 'Wizard Banco Sudameris'

    name = fields.Char(string='Nombre', required=True)
    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)
    tipo_novedades_ids = fields.Many2many('hr.novedades.tipo', string='Tipos de Novedades', required=True)

    def print_wizard_bancos_sudameris_report(self):
        return self.env.ref('rrhh_payroll_bancos_sudameris.wizard_bancos_sudameris_report').report_action(self)

    def get_values_for_report_bancos_sudameris(self):
        def get_formatted_string_left(text, lenght, fill_character=' '):
            text = text or ' '
            return text
            #return text[:lenght].ljust(lenght, fill_character)

        def get_formatted_string_right(text, lenght, fill_character='0'):
            text = text or '0'
            return text
            #return text[:lenght].rjust(lenght, fill_character)

        novedades_all = self.env['hr.novedades'].search([
            ('state', 'in', ['done', 'procesado']),
            ('tipo_id', 'in', self.tipo_novedades_ids.ids),
            ('fecha', '>=', self.date_from),
            ('fecha', '<=', self.date_to),
        ]).filtered(lambda x: x.employee_id.bank_id == self.env.ref('reportes_ministerio_trabajo_py.banco_sudameris'))

        final_text = ''

        if not novedades_all:
            return final_text

        c = 0
        fecha_servicio = max(novedades_all.mapped('fecha'))
        referencia = str(fecha_servicio.year)
        referencia += str(fecha_servicio.month).rjust(2, '0')
        referencia += str(fecha_servicio.day)[0]
        referencia += '1'
        referencia += '0'
        referencia += self.env.user.company_id.banco_sudameris_cod_contrato
        referencia = referencia[:18]
        fecha_servicio = datetime.date.strftime(fecha_servicio, '%d/%m/%y')

        for contract in novedades_all.mapped('contract_id'):
            novedades_contract = novedades_all.filtered(lambda novedad: novedad.contract_id == contract)
            total_linea = int(sum(novedades_contract.mapped('monto')))
            if total_linea:
                c += 1
                final_text += '\n'
                final_text += 'D;'
                final_text += get_formatted_string_left('PAGO DE SALARIO VIA BANCO', 30)
                final_text += ';'
                final_text += get_formatted_string_left(
                    (' '.join(contract.employee_id.apellido.split(' ')[:1]) if len(contract.employee_id.apellido.split(' ')) > 0 else ''), 15)
                final_text += ';'
                final_text += get_formatted_string_left(
                    (' '.join(contract.employee_id.apellido.split(' ')[1:]) if len(contract.employee_id.apellido.split(' ')) > 1 else ''), 15)
                final_text += ';'
                final_text += get_formatted_string_left(
                    (' '.join(contract.employee_id.nombre.split(' ')[:1]) if len(contract.employee_id.nombre.split(' ')) > 0 else ''), 15)
                final_text += ';'
                final_text += get_formatted_string_left(
                    (' '.join(contract.employee_id.nombre.split(' ')[1:]) if len(contract.employee_id.nombre.split(' ')) > 1 else ''), 15)
                final_text += ';'
                final_text += get_formatted_string_right('586', 3)
                final_text += ';'
                final_text += get_formatted_string_right('1', 2)
                final_text += ';'
                final_text += get_formatted_string_left(contract.employee_id.identification_id, 15)
                final_text += ';'
                final_text += get_formatted_string_right('6900', 4)
                final_text += ';'
                final_text += get_formatted_string_right((str(total_linea) + '.00'), 18)
                final_text += ';'
                final_text += get_formatted_string_left(datetime.date.strftime(max(novedades_contract.mapped('fecha')), '%d/%m/%y'), 8)
                final_text += ';'
                final_text += get_formatted_string_right('21', 3)
                final_text += ';'
                final_text += get_formatted_string_right(contract.employee_id.bank_account, 9)
                final_text += ';'
                final_text += get_formatted_string_right('10', 3)
                final_text += ';'
                final_text += get_formatted_string_right('6900', 4)
                final_text += ';'
                final_text += get_formatted_string_right('', 9)
                final_text += ';'
                final_text += get_formatted_string_right('', 3)
                final_text += ';'
                final_text += get_formatted_string_right('', 3)
                final_text += ';'
                final_text += get_formatted_string_left(referencia, 18)  # REFERENCIA
                final_text += ';'
                final_text += get_formatted_string_right('1', 3)
                final_text += ';'
                final_text += get_formatted_string_right((str(total_linea) + '.00'), 18)
                final_text += ';'
                final_text += get_formatted_string_left('31/12/99', 8)
                final_text += ';'
                final_text += get_formatted_string_left(datetime.date.strftime(contract.date_start, '%d/%m/%y'), 8)

        first_line = 'H'
        first_line += get_formatted_string_right(self.env.user.company_id.banco_sudameris_cod_contrato, 9)
        first_line += ';'
        first_line += get_formatted_string_left(self.env.user.company_id.banco_sudameris_email_asociado, 50)
        first_line += ';'
        first_line += get_formatted_string_right('6900', 4)
        first_line += ';'
        final_text += get_formatted_string_right((str(int(sum(novedades_all.mapped('monto')))) + '.00'), 18)
        first_line += ';'
        first_line += get_formatted_string_right(str(c), 5)
        first_line += ';'
        first_line += get_formatted_string_left(fecha_servicio, 8)
        first_line += ';'
        first_line += get_formatted_string_left(referencia, 18)  # REFERENCIA
        first_line += ';'
        first_line += get_formatted_string_right('1', 3)
        first_line += ';'
        first_line += get_formatted_string_right('1', 1)
        first_line += ';'
        first_line += get_formatted_string_right(self.env.user.company_id.banco_sudameris_nro_cuenta, 9)
        first_line += ';'
        first_line += get_formatted_string_right('10', 3)
        first_line += ';'
        first_line += get_formatted_string_right('20', 3)
        first_line += ';'
        first_line += get_formatted_string_right('6900', 4)
        first_line += ';'
        first_line += get_formatted_string_right('0', 9)
        first_line += ';'
        first_line += get_formatted_string_right('0', 3)
        first_line += ';'
        first_line += get_formatted_string_right('0', 3)

        final_text = first_line + final_text
        return final_text
