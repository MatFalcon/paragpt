from odoo import models, fields, api, exceptions
import datetime


class HRPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def get_values_for_report_bancos_familiar(self):
        def get_formatted_string_left(text, lenght, fill_character=' '):
            text = text or ''
            return text[:lenght].ljust(lenght, fill_character)

        def get_formatted_string_right(text, lenght, fill_character='0'):
            text = text or ''
            return text[:lenght].rjust(lenght, fill_character)

        final_text = ''

        payslips_all = self.slip_ids.filtered(
            lambda x: x.state in ['done', 'paid'] and x.employee_id.bank_id == self.env.ref('reportes_ministerio_trabajo_py.banco_familiar')
        )
        if not payslips_all:
            return final_text

        c = 0

        for contract in payslips_all.mapped('contract_id'):
            payslips_contract = payslips_all.filtered(lambda payslip: payslip.contract_id == contract)
            total_linea = int(sum(payslips_contract.line_ids.filtered(lambda x: x.code in ['NET']).mapped('total')))
            if total_linea:
                c += 1
                final_text += '\n'
                final_text += ' CI'
                final_text += get_formatted_string_left(contract.employee_id.identification_id, 15)
                final_text += get_formatted_string_left(', '.join([contract.employee_id.apellido, contract.employee_id.nombre]), 80)
                final_text += get_formatted_string_right((str(total_linea)), 18)
                final_text += '00'
                final_text += get_formatted_string_left('', 200)

        first_line = 'PS'
        first_line += get_formatted_string_right(str(c), 3)
        first_line += get_formatted_string_left(','.join(payslip_run.name for payslip_run in self), 20)
        payslip_dates = payslips_all.mapped('date_to')
        payslip_dates.append(datetime.date.today())
        first_line += get_formatted_string_right(datetime.date.strftime(max(payslip_dates), '%Y%m%d'), 8)
        first_line += 'S'
        first_line += 'PYG'
        first_line += get_formatted_string_left(self.company_id.banco_familiar_nro_cuenta, 11)
        first_line += get_formatted_string_left('', 200)

        final_text = first_line + final_text
        return final_text
