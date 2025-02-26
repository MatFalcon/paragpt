# -*- coding: utf-8 -*-

from . import report
from . import controllers
from . import models

from odoo import api, SUPERUSER_ID


def reportes_ministerio_trabajo_py_post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for company in env['res.company'].search([]):
        company.payroll_structure_default_vacacion = env.ref('reportes_ministerio_trabajo_py.estructura_vacaciones')
        company.payroll_structure_default_aguinaldo = env.ref('reportes_ministerio_trabajo_py.estructura_aguinaldo')
