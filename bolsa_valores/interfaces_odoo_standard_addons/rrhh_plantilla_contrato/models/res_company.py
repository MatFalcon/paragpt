# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api
import re
from datetime import datetime, date


class ResCompany(models.Model):
    _inherit = 'res.company'

    representante_legal_nacionalidad = fields.Many2one(
        'res.country', 'Nacionalidad (Pais)', groups="hr.group_hr_user", tracking=True)
    representante_legal_gender = fields.Selection([
        ('masculino', 'Masculino'),
        ('femenino', 'Femenino'),
        ('otro', 'Otro')
    ], groups="hr.group_hr_user", default="masculino", tracking=True, string='Género')
    representante_legal_marital = fields.Selection([
        ('casado/a', 'Casado(a)'),
        ('soltero/a', 'Soltero(a)'),
        ('viudo/a', 'Viudo(a)'),
        ('divorciado/a', 'Divorciado(a)'),
        ('cohabitante', 'Cohabitante legal'),
        ('no-asignado', 'No Asignado'),
        ('separado/a', 'Separado(a)'),
        ('menor', 'Menor'),
        ('difunto/a', 'Difunto(a)'),
        ('no-aplica', 'No Aplica'),
    ], string='Estado Civil', groups="hr.group_hr_user", default='soltero/a', tracking=True)

    representante_legal_identification_id = fields.Char(string='Nº identificación', groups="hr.group_hr_user", tracking=True)
    representante_legal_profesion = fields.Char(string="Profesión / Oficio")
    representante_legal_birthday = fields.Date('Fecha de nacimiento', groups="hr.group_hr_user", tracking=True)
    representante_legal_edad = fields.Integer(string="Edad", compute="compute_edad")
    representante_legal_nombre = fields.Char(string='Nombres')
    representante_legal_apellido = fields.Char(string='Apellidos')
    representante_legal_direccion = fields.Char('Dirección')

    vat_no_verification_digit = fields.Char(compute='_get_vat_no_verification_digit')

    representante_legal_pronouns_o_a = fields.Char(compute='_get_pronounses')
    representante_legal_pronouns_el_la_senor_ra = fields.Char(compute='_get_pronounses')
    representante_legal_pronouns_el_la_empleador_ra = fields.Char(compute='_get_pronounses')

    def _get_pronounses(self):
        for this in self:
            if this.representante_legal_gender == 'femenino':
                this.representante_legal_pronouns_o_a = 'a'
                this.representante_legal_pronouns_el_la_senor_ra = 'La Señora'
                this.representante_legal_pronouns_el_la_empleador_ra = 'LA EMPLEADORA'
            else:
                this.representante_legal_pronouns_o_a = 'o'
                this.representante_legal_pronouns_el_la_senor_ra = 'El Señor'
                this.representante_legal_pronouns_el_la_empleador_ra = 'EL EMPLEADOR'

    def _get_vat_no_verification_digit(self):
        for this in self:
            this.vat_no_verification_digit = this.vat.split('-')[0] if this.vat else ''

    @api.depends('representante_legal_birthday')
    def compute_edad(self):
        for i in self:
            if i.representante_legal_birthday:
                fecha_nacimiento = i.representante_legal_birthday
                hoy = date.today()
                edad_actual = (hoy - fecha_nacimiento).days
                i.representante_legal_edad = int(edad_actual / 365)
            else:
                i.representante_legal_edad = 0
