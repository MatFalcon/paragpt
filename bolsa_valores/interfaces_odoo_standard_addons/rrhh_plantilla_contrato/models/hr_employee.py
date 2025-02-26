# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api
import re


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    pronouns_o_a = fields.Char(compute='_get_pronounses')
    pronouns_el_la = fields.Char(compute='_get_pronounses')
    pronouns_el_la_senor_ra = fields.Char(compute='_get_pronounses')
    pronouns_el_la_empleado_a = fields.Char(compute='_get_pronounses')
    pronouns_el_la_trabajador_ra = fields.Char(compute='_get_pronounses')

    def _get_pronounses(self):
        for this in self:
            if this.gender == 'female':
                this.pronouns_o_a = 'a'
                this.pronouns_el_la = 'LA'
                this.pronouns_el_la_senor_ra = 'La Señora'
                this.pronouns_el_la_empleado_a = 'LA EMPLEADA'
                this.pronouns_el_la_trabajador_ra = 'LA TRABAJADORA'
            else:
                this.pronouns_o_a = 'o'
                this.pronouns_el_la = 'EL'
                this.pronouns_el_la_senor_ra = 'El Señor'
                this.pronouns_el_la_empleado_a = 'EL EMPLEADO'
                this.pronouns_el_la_trabajador_ra = 'EL TRABAJADOR'

    # def init(self):
    #     for this in self.search([]):
    #         this.update({'new_marital': this.marital})

    # gender = fields.Selection(selection=[
    #     ('male', 'Masculino'),
    #     ('female', 'Femenino'),
    #     ('other', 'Otro')
    # ], groups="hr.group_hr_user", tracking=True)
    # new_gender = fields.Selection(selection=[('male', 'Masculino'), ('female', 'Femenino')], string='Sexo',
    #                               groups="hr.group_hr_user", default="male", tracking=True)
    gender_show = fields.Char(compute="get_gender_show")
    marital_show = fields.Char(compute="get_marital_show")

    # marital = fields.Selection(selection_add=[
    #     ('soltero/a', 'Soltero/a'),
    #     ('casado/a', 'Casado/a'),
    #     ('cohabitante', 'Cohabitante Legal'),
    #     ('viudo/a', 'Viudo/a'),
    #     ('divorciado/a', 'Divorciado/a'),
    #     ('menor', 'Menor')
    # ], string='Estado Civil', groups="hr.group_hr_user", tracking=True)
    # new_marital = fields.Selection(selection=[
    #     ('soltero/a', 'Soltero/a'),
    #     ('casado/a', 'Casado/a'),
    #     ('cohabitante', 'Cohabitante Legal'),
    #     ('viudo/a', 'Viudo/a'),
    #     ('divorciado/a', 'Divorciado/a'),
    #     ('menor', 'Menor')
    # ], string='Estado Civil', groups="hr.group_hr_user")

    # def set_marital_state(self):
    #     for this in self:
    #         if this.marital != this.new_marital:
    #             this.marital = this.new_marital

    # @api.model
    # def create(self, vals):
    #     r = super(HrEmployee, self).create(vals)
    #     r.set_marital_state()
    #     return r
    #
    # def write(self, vals):
    #     r = super(HrEmployee, self).write(vals)
    #     self.set_marital_state()
    #     return r
    #
    def get_gender_show(self):
        for this in self:
            if this.gender == 'male':
                this.gender_show = 'masculino'
            elif this.gender == 'female':
                this.gender_show = 'femenino'
            else:
                this.gender_show = 'otro'

    def get_marital_show(self):
        for this in self:
            if this.marital == 'married':
                this.marital_show = 'Casado/a'
            elif this.marital == 'cohabitant':
                this.marital_show = 'Cohabitante Legal'
            elif this.marital == 'widower':
                this.marital_show = 'Viudo/a'
            elif this.marital == 'divorced':
                this.marital_show = 'Divorciado/a'
            else:
                this.marital_show = 'Soltero/a'
