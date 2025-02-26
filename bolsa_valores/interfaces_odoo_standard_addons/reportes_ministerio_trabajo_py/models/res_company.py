# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'res.company'

    nro_patronal = fields.Char(string='Nro. Patronal')
    patronal_mtess_actividad = fields.Char(string='Actividad MTESS')
    nro_ips = fields.Char(string='Nro. IPS')
    patronal_ips_actividad = fields.Char(string='Actividad IPS')

    payroll_structure_default_vacacion = fields.Many2one(
        'hr.payroll.structure',
        string='Estructura para Vacaciones',
    )
    payroll_structure_default_aguinaldo = fields.Many2one(
        'hr.payroll.structure',
        string='Estructura para Aguinaldos',
    )

    base_aguinaldo_descuentos = fields.Char(
        'Códigos a descontar del bruto para la base del aguinaldo',
        default='BF,AUS,SUNP,AMON,SAA,LLT'
    )

    sueldos_y_jornales_report_dias_sabado_valor = fields.Selection(
        [
            ('normal', 'Valor Normal'),
            ('0', '0 Horas'),
            ('4', '4 Horas'),
            ('8', '8 Horas'),
        ],
        string='Valor para los días Sábados en el reporte de Sueldos y Jornales',
        default='normal'
    )

    sueldos_y_jornales_report_codigos_hex_50 = fields.Char(
        'Códigos para la columna Horas Extra 50%',
        default='HEX50',
    )
    sueldos_y_jornales_report_codigos_hex_100 = fields.Char(
        'Códigos para la columna Horas Extra 100%',
        default='HEX100',
    )
    sueldos_y_jornales_report_codigos_hex_otros = fields.Char(
        'Códigos para la columna Otras Horas Extra (Valor)',
        default='HNOC,HEXNOC',
    )
    sueldos_y_jornales_report_codigos_bonificacion_familiar = fields.Char(
        'Códigos para la columna Bonificación Familiar',
        default='BF',
    )
    sueldos_y_jornales_report_codigos_otros_beneficios = fields.Char(
        'Códigos para la columna Otros Beneficios',
        default='PREAV,INDEM,VACPRO,OB,OTRH,OIS,AGUIPR',
    )

    def write(self, values):
        for field in (
                'base_aguinaldo_descuentos',
                'sueldos_y_jornales_report_codigos_hex_50',
                'sueldos_y_jornales_report_codigos_hex_100',
                'sueldos_y_jornales_report_codigos_hex_otros',
                'sueldos_y_jornales_report_codigos_bonificacion_familiar',
                'sueldos_y_jornales_report_codigos_otros_beneficios',
        ):
            if field in values:
                if values.get(field):
                    values.update({field: values.get(field).replace(' ', '')})
        return super(HrEmployee, self).write(values)
