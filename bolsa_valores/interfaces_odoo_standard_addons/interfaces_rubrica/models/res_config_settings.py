from odoo import api, fields, models, release


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    if release.major_version in ['16.0']:
        reporte_libro_inventario_base_report_bg = fields.Many2one(
            'account.report',
            string='Reporte base para el Balance General',
            related='company_id.reporte_libro_inventario_base_report_bg',
            help='Estructura de reportes que se utilizará para el Balance General en el reporte de Libro Inventario',
            readonly=False
        )
        reporte_libro_inventario_base_report_er = fields.Many2one(
            'account.report',
            string='Reporte base para el Estado de Resultados',
            related='company_id.reporte_libro_inventario_base_report_er',
            help='Estructura de reportes que se utilizará para el Estado de Resultados en el reporte de Libro Inventario',
            readonly=False
        )
    if release.major_version in ['15.0']:
        reporte_libro_inventario_base_report_bg = fields.Many2one(
            'account.financial.html.report',
            string='Reporte base para el Balance General',
            related='company_id.reporte_libro_inventario_base_report_bg',
            help='Estructura de reportes que se utilizará para el Balance General en el reporte de Libro Inventario',
            readonly=False
        )
        reporte_libro_inventario_base_report_er = fields.Many2one(
            'account.financial.html.report',
            string='Reporte base para el Estado de Resultados',
            related='company_id.reporte_libro_inventario_base_report_er',
            help='Estructura de reportes que se utilizará para el Estado de Resultados en el reporte de Libro Inventario',
            readonly=False
        )

    show_libro_inventario_base_report_bg_details = fields.Boolean(
        string='Mostrar detalles de cuentas',
        related='company_id.show_libro_inventario_base_report_bg_details',
        help='Detallar la composición de las cuentas listadas: saldos pendientes, cantidades de inventario, listado de activos fijos, etc.',
        readonly=False
    )
