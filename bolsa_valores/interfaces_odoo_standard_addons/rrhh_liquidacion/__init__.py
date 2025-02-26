# -*- coding: utf-8 -*-

from . import models


def rrhh_liquidacion_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].search([]):
        company.payroll_structure_default_despido = env.ref('rrhh_liquidacion.estructura_despido')
        company.payroll_structure_default_renuncia = env.ref('rrhh_liquidacion.estructura_renuncia')
