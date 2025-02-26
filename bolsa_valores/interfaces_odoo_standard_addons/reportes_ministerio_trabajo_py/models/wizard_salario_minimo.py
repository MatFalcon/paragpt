from odoo import fields, api, models
import datetime


class WizSalarioMinimo(models.Model):
    _name = 'wizard_salario_minimo'
    _description = 'Wizard para definir los salario minimos y las fechas de inicio de los mismos'

    line_ids = fields.One2many('salarios_minimos', 'wizard_id', string='Salarios mínimos', default=lambda self: self.obtener_salarios_actuales(),
                               relation='wizard_salario_minimo_lines_rel')

    def obtener_salarios_actuales(self):
        # reportes_ministerio_trabajo_py/models/wizard_salario_minimo.py
        return self.env['salarios_minimos'].search([])

    def button_actualizar_salarios(self):
        # reportes_ministerio_trabajo_py/models/wizard_salario_minimo.py
        self.env['salarios_minimos'].search([('id', 'not in', self.line_ids.ids)]).unlink()

    def get_salario_vigente(self, request_date):
        # reportes_ministerio_trabajo_py/models/wizard_salario_minimo.py
        salario_vigente = 0
        if request_date:
            if isinstance(request_date, datetime.datetime):
                request_date = request_date.date()
            for salario in self.env['salarios_minimos'].search([]):
                if request_date >= salario.date_from:
                    salario_vigente = salario.amount
        return salario_vigente


class SalariosMinimos(models.Model):
    _name = 'salarios_minimos'
    _description = 'Líneas de salarios con sus vigencias'
    _order = "date_from asc"

    wizard_id = fields.Many2one('wizard_salario_minimo')
    date_from = fields.Date(string='Vigente desde', required=True)
    amount = fields.Integer(string='Monto', required=True)
