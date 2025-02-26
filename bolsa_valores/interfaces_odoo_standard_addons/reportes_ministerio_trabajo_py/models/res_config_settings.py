from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    payroll_structure_default_vacacion = fields.Many2one(
        'hr.payroll.structure',
        string='Estructura para Vacaciones',
        related='company_id.payroll_structure_default_vacacion',
        help='Estructura que se utilizará por defecto para las nóminas de Vacaciones',
        readonly=False
    )
    payroll_structure_default_aguinaldo = fields.Many2one(
        'hr.payroll.structure',
        string='Estructura para Aguinaldos',
        related='company_id.payroll_structure_default_aguinaldo',
        help='Estructura que se utilizará por defecto para las nóminas de Aguinaldos',
        readonly=False
    )

    base_aguinaldo_descuentos = fields.Char(
        'Códigos a descontar del bruto para la base del aguinaldo',
        related='company_id.base_aguinaldo_descuentos',
        help='Códigos a descontar del bruto para la base del aguinaldo',
        readonly=False
    )

    sueldos_y_jornales_report_dias_sabado_valor = fields.Selection(
        [
            ('normal', 'Valor Normal'),
            ('0', '0 Horas'),
            ('4', '4 Horas'),
            ('8', '8 Horas'),
        ],
        string='Valor para los días Sábados en el reporte de Sueldos y Jornales',
        related='company_id.sueldos_y_jornales_report_dias_sabado_valor',
        help='Normal: La letra o número mostrado en los días sábados será calculado dependiendo de sus vacaciones, reposos, ausencias, etc. Cualquier otra opción forzará el valor a ser mostrado',
        readonly=False
    )
    sueldos_y_jornales_report_codigos_hex_50 = fields.Char(
        'Códigos para la columna Horas Extra 50%',
        related='company_id.sueldos_y_jornales_report_codigos_hex_50',
        help='Códigos de las Reglas Salariales que se deben de sumar para obtener el valor de la columna Horas Extra 50% en el reporte de Sueldos y Jornales',
        readonly=False
    )
    sueldos_y_jornales_report_codigos_hex_100 = fields.Char(
        'Códigos para la columna Horas Extra 100%',
        related='company_id.sueldos_y_jornales_report_codigos_hex_100',
        help='Códigos de las Reglas Salariales que se deben de sumar para obtener el valor de la columna Horas Extra 100% en el reporte de Sueldos y Jornales',
        readonly=False
    )
    sueldos_y_jornales_report_codigos_hex_otros = fields.Char(
        'Códigos para la columna Otras Horas Extra (Valor)',
        related='company_id.sueldos_y_jornales_report_codigos_hex_otros',
        help='Códigos de las Reglas Salariales que se deben de sumar para obtener el valor de la columna Otras Horas Extra en el reporte de Sueldos y Jornales',
        readonly=False
    )
    sueldos_y_jornales_report_codigos_bonificacion_familiar = fields.Char(
        'Códigos para la columna Bonificación Familiar',
        related='company_id.sueldos_y_jornales_report_codigos_bonificacion_familiar',
        help='Códigos de las Reglas Salariales que se deben de sumar para obtener el valor de la columna Bonificación Familiar en el reporte de Sueldos y Jornales',
        readonly=False
    )
    sueldos_y_jornales_report_codigos_otros_beneficios = fields.Char(
        'Códigos para la columna Otros Beneficios',
        related='company_id.sueldos_y_jornales_report_codigos_otros_beneficios',
        help='Códigos de las Reglas Salariales que se deben de sumar para obtener el valor de la columna Otros Beneficios en el reporte de Sueldos y Jornales',
        readonly=False
    )
