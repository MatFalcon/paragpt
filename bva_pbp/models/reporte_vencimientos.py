from odoo import models, fields, api
from odoo.exceptions import UserError
class ReporteVencimientos(models.Model):
    _name = 'pbp.reporte_vencimientos'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Se almacenan los reportes de vencimientos'
    """
        En este modelo se almacenaran los reportes de vencimientos,
        para tener un historial de los reporte generados.
    """
    name = fields.Char(string='Nombre', required=True)
    fecha_inicio = fields.Date(string='Fecha Inicio')
    fecha_fin = fields.Date(string='Fecha Fin')
    fecha_plazo = fields.Date(string='Fecha Plazo')
    state = fields.Selection(
        selection=[
            ('prueba', 'Prueba'),
            ('aprobado', 'Aprobado'),
        ], default='prueba',
        tracking=True)
    reporte_excel_filename = fields.Char(string="Nombre de archivo", related='name')
    reporte_excel = fields.Binary(string="Reporte Excel", readonly=True)    


    def unlink(self):
        for rec in self:
            if rec.state == 'aprobado':
                raise UserError("No puede eliminar el registro en estado Aprobado")
        return super(ReporteVencimientos, self).unlink()
    

    def create(self, vals):
        res = super(ReporteVencimientos, self).create(vals)
        creado_en_periodo = self.env['pbp.reporte_vencimientos'].search([
            ('fecha_plazo', '<=', self.fecha_plazo),
            ('fecha_plazo', '>=', self.fecha_plazo),
            ('state', '=', 'aprobado'),
        ])
        if creado_en_periodo:
            raise UserError('Ya existe un reporte en este periodo')

        return res

    def write(self, vals):
        if 'fecha_plazo' in vals or 'state' in vals:
            fecha_plazo = vals.get('fecha_plazo', self.fecha_plazo)
            state = vals.get('state', self.state)
            creado_en_periodo = self.env['pbp.reporte_vencimientos'].search([
                ('fecha_plazo', '<=', fecha_plazo),
                ('fecha_plazo', '>=', fecha_plazo),
                ('state', '=', 'aprobado'),
            ])
            if creado_en_periodo:
                raise UserError('Ya existe un reporte en este periodo')
        return super(ReporteVencimientos, self).write(vals)
    
    def aprobar_reporte(self):
        self.state = 'aprobado'
