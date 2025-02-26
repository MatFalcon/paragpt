from odoo import models, fields

class Resolucion(models.Model):
    _name = 'resolucion'
    _description = 'Resoluciones'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Nombre", required=True, tracking=True)
    cliente = fields.Many2one('res.partner', string="Cliente", required=True, tracking=True)
    fecha_creacion = fields.Date(string="Fecha de Creación", default=fields.Date.context_today, required=True, tracking=True)
    fecha_vencimiento = fields.Date(string="Fecha de Vencimiento", required=True, tracking=True)
    codigo = fields.Char(string="Código", required=True, tracking=True)
    pbp_novedades_sen_id = fields.Many2one('pbp.novedades_sen', string='Custodia Anual')
    novedades_sen_ids = fields.One2many('pbp.novedades_sen', 'resolucion_id', string='Novedades Sen', tracking=True)
