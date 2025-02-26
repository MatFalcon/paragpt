from odoo import models, fields, api, exceptions


class CalculoFondoGarantia(models.Model):
    _name = 'pbp.calculo_fondo_garantia'
    _rec_name = 'id_pbp'

    id_pbp = fields.Integer(string='ID Comision', copy=False)
    id_vvalores = fields.Integer(string='ID vValores')
    mercado = fields.Char(string="Mercado")
    instrumento = fields.Char(string="Instrumento")
    volumen_negociado = fields.Monetary(string="Volumen negociado")
    fecha_operacion = fields.Date(string='Fecha de operación')
    fecha_vencimiento = fields.Date(string='Fecha de vencimiento')
    cliente_id = fields.Integer(string="ID Cliente PBP")
    plazo = fields.Integer(compute='compute_plazo', string="Plazo")
    calculo = fields.Monetary(compute='compute_calculo', string="Cálculo")
    total = fields.Monetary(string="Total")
    inicio_periodo = fields.Date(required=False, string='Inicio del periodo')
    fin_periodo = fields.Date(required=False, string='Fin del periodo')



    currency_id = fields.Many2one('res.currency', required=True, string="Moneda")
    partner_id = fields.Many2one('res.partner', string="Cliente")

    @api.depends('fecha_operacion', 'fecha_vencimiento')
    def compute_plazo(self):
        for calculo in self:
            if calculo.fecha_operacion and calculo.fecha_vencimiento:
                calculo.plazo = (calculo.fecha_vencimiento - calculo.fecha_operacion).days
            else:
                calculo.plazo = False

    @api.depends('plazo', 'volumen_negociado')
    def compute_calculo(self):
        for calculo in self:
            if calculo.plazo and calculo.volumen_negociado:
                calculo.calculo = calculo.volumen_negociado / 100 * 0.005 / 365 * calculo.plazo
            else:
                calculo.calculo = False
