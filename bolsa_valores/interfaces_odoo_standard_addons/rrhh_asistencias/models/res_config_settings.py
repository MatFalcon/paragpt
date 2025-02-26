from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    overtime_employee_threshold_early_leaves = fields.Integer(
        string='Tiempo de tolerancia para salidas anticipadas',
        related='company_id.overtime_employee_threshold_early_leaves',
        help='Tolerancia para las salidas anticipadas de los empleados',
        readonly=False
    )

    considerar_horas_nocturnas_en_planeado = fields.Boolean(
        string='Considerar Horas Nocturnas dentro del horario planeado',
        config_parameter='considerar_horas_nocturnas_en_planeado'
    )
    considerar_llegada_anticipada = fields.Boolean(
        string='Considerar llegada anticipada',
        config_parameter='considerar_llegada_anticipada'
    )
    considerar_llegada_tardia = fields.Boolean(
        string='Considerar llegada tardia',
        config_parameter='considerar_llegada_tardia'
    )
    considerar_salida_anticipada = fields.Boolean(
        string='Considerar salida anticipada',
        config_parameter='considerar_salida_anticipada'
    )
    considerar_horas_extra_50 = fields.Boolean(
        string='Considerar horas extra 50%',
        config_parameter='considerar_horas_extra_50'
    )
    considerar_horas_extra_100 = fields.Boolean(
        string='Considerar horas extra 100%',
        config_parameter='considerar_horas_extra_100'
    )
    considerar_horas_extra_nocturnas = fields.Boolean(
        string='Considerar horas extra Nocturnas',
        config_parameter='considerar_horas_extra_nocturnas'
    )
    considerar_horas_nocturnas = fields.Boolean(
        string='Considerar horas extra 100%',
        config_parameter='considerar_horas_nocturnas'
    )
    considerar_plus_hora = fields.Boolean(
        string='Considerar plus de horas',
        config_parameter='considerar_plus_hora'
    )
    considerar_mix_hora = fields.Boolean(
        string='Considerar plus de horas',
        config_parameter='considerar_mix_hora'
    )
    inicio_plus = fields.Float(
        string='Inicio de horario plus',
        config_parameter='inicio_plus'
    )
    fin_plus = fields.Float(
        string='Fin de horario plus',
        config_parameter='fin_plus'
    )
    inicio_mix = fields.Float(
        string='Inicio de horario mixto',
        config_parameter='inicio_mix'
    )
    fin_mix = fields.Float(
        string='Fin de horario mixto',
        config_parameter='fin_mix'
    )
