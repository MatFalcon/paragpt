from odoo import api, fields, models
import datetime


class WizardBancoItau(models.TransientModel):
    _name = 'wizard_bancos_itau'
    _description = 'Wizard Banco Itau'

    name = fields.Char(string='Nombre', required=True)
    date_from = fields.Date(string='Fecha Desde', required=True)
    date_to = fields.Date(string='Fecha Hasta', required=True)
    tipo_novedades_ids = fields.Many2many('hr.novedades.tipo', string='Tipos de Novedades', required=True)

    def print_wizard_bancos_itau_report(self):
        return self.env.ref('rrhh_payroll_bancos_itau.wizard_bancos_itau_report').report_action(self)

    def get_values_for_report_bancos_itau(self):
        def change_characters(text):
            allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,1234567890'
            for character_pair in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ñ', 'n')]:
                text = text.replace(character_pair[0], character_pair[1])
                text = text.replace(character_pair[0].upper(), character_pair[1].upper())
            for character in text:
                if character not in allowed_characters:
                    text = text.replace(character, ' ')
            return text

        def get_formatted_string_left(text, lenght, fill_character=' '):
            text = change_characters(text or '')
            return text[:lenght].ljust(lenght, fill_character)

        def get_formatted_string_right(text, lenght, fill_character='0'):
            text = change_characters(text or '')
            return text[:lenght].rjust(lenght, fill_character)

        if not self.env.user.company_id.banco_itau_codigo_empresa:
            raise exceptions.ValidationError('En la empresa debe de establecer un "Código Empresa" (Asignado por ITAU)')

        novedades_all = self.env['hr.novedades'].search([
            ('state', 'in', ['done', 'procesado']),
            ('tipo_id', 'in', self.tipo_novedades_ids.ids),
            ('fecha', '>=', self.date_from),
            ('fecha', '<=', self.date_to),
        ]).filtered(lambda x: x.employee_id.bank_id == self.env.ref('reportes_ministerio_trabajo_py.banco_itau'))

        final_text = ''

        if not novedades_all:
            return final_text

        novedades_dates = novedades_all.mapped('fecha')
        novedades_dates.append(datetime.date.today())

        for contract in novedades_all.mapped('contract_id'):
            novedades_contract = novedades_all.filtered(lambda novedad: novedad.contract_id == contract)
            novedades_contract_amount = int(sum(novedad.monto for novedad in novedades_contract))
            if novedades_contract_amount:
                description = ', '.join(novedad.name.replace('/', ' ') for novedad in novedades_contract)
                final_text += 'D'  # ITIREG
                final_text += '01'  # ITITRA
                final_text += get_formatted_string_right(self.env.user.company_id.banco_itau_codigo_empresa, 3)  # ICDSRV
                final_text += get_formatted_string_right(self.env.user.company_id.banco_itau_nro_cuenta, 10)  # ICTDEB
                final_text += '017'  # IBCOCR
                final_text += get_formatted_string_right(contract.employee_id.bank_account, 10)  # ICTCRE
                final_text += 'C'  # ITCRDB
                final_text += get_formatted_string_left(contract.employee_id.nombre + ' ' + contract.employee_id.apellido, 50)  # IORDEN
                final_text += '0'  # IMONED
                final_text += get_formatted_string_right((str(novedades_contract_amount) + '00'), 15)  # IMTOTR
                final_text += get_formatted_string_right('', 15)  # IMTOT2
                final_text += get_formatted_string_left((contract.employee_id.identification_id), 12)  # INRODO
                final_text += '0'  # ITIFAC
                final_text += get_formatted_string_left('', 20)  # INRFAC
                final_text += '000'  # INRCUO
                final_text += get_formatted_string_right(datetime.date.strftime(max(novedades_dates), '%Y%m%d'), 8)  # IFCHCR
                final_text += get_formatted_string_right('', 8)  # IFCHC2
                final_text += get_formatted_string_left('', 50)  # ICEPTO
                final_text += get_formatted_string_left(description, 15)  # INRREF
                final_text += get_formatted_string_right(datetime.date.strftime(max(novedades_dates), '%Y%m%d'), 8)  # IFECCA
                final_text += get_formatted_string_right('080000', 6)  # IHORCA
                final_text += get_formatted_string_left('', 10)  # IUSUCA
                final_text += '\n'
        final_text += 'C'  # ITIREG
        final_text += '00'  # ITITRA
        final_text += get_formatted_string_right('', 3)  # ICDSRV
        final_text += get_formatted_string_right(self.env.user.company_id.banco_itau_nro_cuenta, 10)  # ICTDEB
        final_text += '000'  # IBCOCR
        final_text += get_formatted_string_right('', 10)  # ICTCRE
        final_text += ' '  # ITCRDB
        final_text += get_formatted_string_left('', 50)  # IORDEN
        final_text += '0'  # IMONED
        final_text += get_formatted_string_right((str(int(sum(novedades_all.mapped('monto')))) + '00'), 15)  # IMTOTR
        final_text += get_formatted_string_right('', 15)  # IMTOT2
        final_text += get_formatted_string_left('', 12)  # INRODO
        final_text += '0'  # ITIFAC
        final_text += get_formatted_string_left('', 20)  # INRFAC
        final_text += '000'  # INRCUO
        final_text += get_formatted_string_left('', 8, '0')  # IFCHCR
        final_text += get_formatted_string_left('', 8, '0')  # IFCHC2
        final_text += get_formatted_string_left('', 50)  # ICEPTO
        final_text += get_formatted_string_left('', 15)  # INRREF
        final_text += get_formatted_string_right(datetime.date.strftime(max(novedades_dates), '%Y%m%d'), 8)  # IFECCA
        final_text += get_formatted_string_right('000000', 6)  # IHORCA
        final_text += get_formatted_string_left('', 10)  # IUSUCA

        return final_text
