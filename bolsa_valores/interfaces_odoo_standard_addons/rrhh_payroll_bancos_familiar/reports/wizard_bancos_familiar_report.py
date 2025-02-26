from odoo import api, fields, models
import datetime


class WizardBancoFamiliar(models.TransientModel):
    _name = 'wizard_bancos_familiar'
    _description = 'Wizard Banco Familiar'

    name = fields.Char(string='Nombre', required=True)
    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)
    tipo_novedades_ids = fields.Many2many('hr.novedades.tipo', string='Tipos de Novedades', required=True)

    def print_wizard_bancos_familiar_report(self):
        return self.env.ref('rrhh_payroll_bancos_familiar.wizard_bancos_familiar_report').report_action(self)

    def get_values_for_report_bancos_familiar(self):
        def get_formatted_string_left(text, lenght, fill_character=' '):
            text = text or ''
            return text[:lenght].ljust(lenght, fill_character)

        def get_formatted_string_right(text, lenght, fill_character='0'):
            text = text or ''
            return text[:lenght].rjust(lenght, fill_character)

        novedades_all = self.env['hr.novedades'].search([
            ('state', 'in', ['done', 'procesado']),
            ('tipo_id', 'in', self.tipo_novedades_ids.ids),
            ('fecha', '>=', self.date_from),
            ('fecha', '<=', self.date_to),
        ]).filtered(lambda x: x.employee_id.bank_id == self.env.ref('reportes_ministerio_trabajo_py.banco_familiar'))

        final_text = ''

        if not novedades_all:
            return final_text

        c = 0

        for contract in novedades_all.mapped('contract_id'):
            novedades_contract = novedades_all.filtered(lambda novedad: novedad.contract_id == contract)
            total_linea = int(sum(novedades_contract.mapped('monto')))
            if total_linea:
                c += 1
                final_text += '\n'
                final_text += ' CI'
                final_text += get_formatted_string_left(contract.employee_id.identification_id, 15)
                final_text += get_formatted_string_left(', '.join([contract.employee_id.apellido, contract.employee_id.nombre]), 80)
                final_text += get_formatted_string_right(str(total_linea), 18)
                final_text += '00'
                final_text += get_formatted_string_left('', 200)

        first_line = 'PS'
        first_line += get_formatted_string_right(str(len(novedades_all)), 3)
        first_line += get_formatted_string_left(self.name, 20)
        novedades_dates = novedades_all.mapped('fecha')
        novedades_dates.append(datetime.date.today())
        first_line += get_formatted_string_right(datetime.date.strftime(max(novedades_dates), '%Y%m%d'), 8)
        first_line += 'S'
        first_line += 'PYG'
        first_line += get_formatted_string_left(self.env.user.company_id.banco_familiar_nro_cuenta, 11)
        first_line += get_formatted_string_left('', 200)

        final_text = first_line + final_text
        return final_text
