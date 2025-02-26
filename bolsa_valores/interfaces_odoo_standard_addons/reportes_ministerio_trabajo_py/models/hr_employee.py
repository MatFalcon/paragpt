# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
import datetime


class HrEmployeeBase(models.AbstractModel):
    _inherit = 'hr.employee.base'

    nombre = fields.Char(string='Nombres', required=True)
    apellido = fields.Char(string='Apellidos')

    children_ids = fields.One2many('hr.employee.children', 'employee_id', string='Hijos')
    job_id = fields.Many2one(string='Profesión')

    bank_id = fields.Many2one('res.bank', string='Banco principal')
    bank_account = fields.Char(string='Cuenta Bancaria')

    mtess_report_employee_type = fields.Selection([
        ('supervisor', 'Supervisor'),
        ('empleado', 'Empleado'),
        ('obrero', 'Obrero'),
        ('menor', 'Menor'),
    ], string='Tipo de empleado para reportes MTESS', default='empleado', required=True)


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    edad = fields.Integer(string="Edad", compute="compute_edad")
    underage_children_count = fields.Integer(string='Hijos menores de edad', compute='_get_underage_children_count')

    @api.onchange('children_ids')
    def _get_underage_children_count(self, explicit_date=fields.date.today()):
        for this in self:
            underage_children_count = len([children for children in this.children_ids if children._get_age(explicit_date=explicit_date, return_age=True) < 18])
            this.underage_children_count = underage_children_count

    @api.onchange('nombre', 'apellido')
    def set_employee_name(self):
        # reportes_ministerio_trabajo/models/hr_employee.py
        for this in self:
            this.name = this.nombre if this.nombre else ''
            if this.apellido:
                # this.name += ' ' + this.apellido
                this.name = this.apellido + ' ' + this.name

    @api.depends('birthday')
    def compute_edad(self):
        # reportes_ministerio_trabajo/models/hr_employee.py
        for i in self:
            if i.birthday:
                fecha_nacimiento = i.birthday
                hoy = datetime.date.today()
                edad_actual = (hoy - fecha_nacimiento).days
                i.edad = int(edad_actual / 365)
            else:
                i.edad = 0

    def _get_aguinaldo_proporcional(self, year=False):
        # reportes_ministerio_trabajo/models/hr_employee.py
        if not year:
            year = datetime.date.today().year
        for this in self:
            salarios_anteriores = self.env['historial.salario'].search(
                [('contract_id', 'in', this.contract_ids.filtered(lambda z: z.state == 'open').ids),
                 ('state', '=', 'good')]).filtered(
                lambda x: x.date_from.year == year)
            aguinaldo_bruto = sum([x.bruto_para_aguinaldo for x in salarios_anteriores])
            return aguinaldo_bruto / 12


class HREmployeeChildren(models.Model):
    _name = 'hr.employee.children'
    _description = 'Children of employee'

    employee_id = fields.Many2one('hr.employee', required=True)
    name = fields.Char(string='Nombre')
    birthday = fields.Date(string='Fecha de Nacimiento', required=True)
    age = fields.Integer(string='Edad', compute='_get_age')

    @api.onchange('birthday')
    def _get_age(self, explicit_date=fields.date.today(), return_age=False):
        age = 0
        for this in self:
            age = 0
            if this.birthday: age = relativedelta(explicit_date, this.birthday).years
            this.age = age
        if return_age: return age
