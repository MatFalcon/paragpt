from odoo import models, fields, api, exceptions
from datetime import datetime, timedelta


class FondoGarantiasPeriodos(models.Model):
    _name = "pbp.fondo_garantias_periodos"
    _description = "Modelo de Fondo de Garantias por Periodos"
    _order = 'name desc'

    name = fields.Char('Secuencia')
    fecha_inicio = fields.Date(string="Inicio del periodo", default=fields.Date.today(), required=True)
    fecha_fin = fields.Date(string="Fin del periodo", default=fields.Date.today(), required=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True)
    state = fields.Selection(
        selection=[
            ('nuevo', 'Nuevo'),
            ('confirmado', 'Confirmado'),
        ], default="nuevo"
    )
    fondo_garantia_ids = fields.One2many('pbp.fondo_garantias', 'periodo_id', string="Lineas")

    rendimiento_mes = fields.Float(string="Rendimiento del mes", compute="compute_rendimiento_mes")
    capital_vencido_mes = fields.Float(string="Capital vencido del mes", compute="compute_capital_vencido_mes")
    egresos_mes = fields.Float(string="Egresos del mes", compute="compute_egresos_mes")

    def compute_rendimiento_mes(self):
        for i in self:
            registros = self.env['pbp.inversion_fondo_garantias'].search([('fecha_actual','>=', i.fecha_inicio),
                                                                         ('fecha_actual','<=',i.fecha_fin)])
            if registros:
                i.rendimiento_mes = sum(registros.mapped('intereses'))
            else:
                i.rendimiento_mes = 0

    def compute_capital_vencido_mes(self):
        for i in self:
            registros = self.env['pbp.inversion_fondo_garantias'].search([('fecha_vencimiento', '>=', i.fecha_inicio),
                                                                         ('fecha_vencimiento', '<=', i.fecha_fin)])
            if registros:
                i.capital_vencido_mes = sum(registros.mapped('capital'))
            else:
                i.capital_vencido_mes = 0

    def compute_egresos_mes(self):
        for i in self:
            diario_fg = self.env['account.journal'].search([('diario_fg','=',True),('currency_id','=', i.currency_id.id)])
            if diario_fg:
                lineas = self.env['account.move.line'].search([('account_id','=',diario_fg.default_account_id),
                                                               ('date','>=',i.fecha_inicio),
                                                               ('date','<=',i.fecha_fin)])
                i.egresos_mes = sum(lineas.filtered(lambda x:x.amount_currency < 0).mapped('amount_currency'))
            else:
                i.egresos_mes = 0

    #def default_name(self):
    #    return self.env['ir.sequence'].sudo().next_by_code('seq_periodo_secuencia_garantias')

    def button_confirmar(self):
        for i in self:
            i.write({'state': 'confirmado'})
        return

    def get_first_date_of_month(self, year, month):
        first_date = datetime(year, month, 1)
        return first_date.date()

    def get_last_date_of_month(self, year, month):
        if month == 12:
            last_date = datetime(year, month, 31)
        else:
            last_date = datetime(year, month + 1, 1) + timedelta(days=-1)
        return last_date.date()

    def generar_registros(self):
        for i in self:
            for x in i.fondo_garantia_ids:
                x.unlink()
            if not i.fecha_inicio or not i.fecha_fin or i.fecha_inicio > i.fecha_fin:
                raise exceptions.ValidationError(
                    'No se pueden obtener registros del mes anterior sin tener correctamente definidas las fechas.'
                    ' Favor verificar')
            else:
                mes_actual = i.fecha_inicio.month
                mes_anterior = mes_actual - 1 if mes_actual != 1 else 12
                year_actual = i.fecha_inicio.year
                year_anterior = i.fecha_inicio.year if mes_actual != 1 else year_actual - 1

                registro_mes_anterior = self.env['pbp.fondo_garantias_periodos'].search([('currency_id','=',i.currency_id.id),
                                                                                         ('fecha_inicio','>=',self.get_first_date_of_month(year_anterior,mes_anterior)),
                                                                                         ('fecha_fin','<=',self.get_last_date_of_month(year_anterior,mes_anterior)),
                                                                                         ('state','=','confirmado')])

                if registro_mes_anterior:
                    for l in registro_mes_anterior.fondo_garantia_ids:
                        vals = {
                            'partner_id':l.partner_id.id,
                            'importe_mes_anterior': l.importe_mes_actual,
                            'periodo_id':i.id
                        }
                        i.write({'fondo_garantia_ids':[(0,0,vals)]})
                #else:
                #    raise exceptions.ValidationError(
                #        'No existen registros anteriores.'
                #        ' Favor verificar')

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        recs = super().create(vals_list)
        for r in recs:
            seq = self.env['ir.sequence'].sudo().next_by_code('seq_periodo_secuencia_garantias')
            r.write({'name':seq})
        return recs


class FondoGarantias(models.Model):
    _name = 'pbp.fondo_garantias'
    _description="Modelo de Fondo de Garantias"

    partner_id = fields.Many2one('res.partner', string="Casa de Bolsa", required=True)

    importe_mes_anterior = fields.Float(string="Importe mes anterior")
    por_participacion_sobre_total = fields.Float(string="Porcentaje de participación sobre el total",
                                                 compute="compute_por_participacion_sobre_total", digits=(12, 12))
    cobro_fg_aporte_cbsa = fields.Float(string="COBRO FG APORTE CBSA (MAYOR)", compute="compute_cobro_fg_aporte_cbsa")
    participacion_sobre_rendimiento = fields.Float(string="Participación sobre rendimiento")
    participacion_egreso_sobre_rendimiento = fields.Float(string="Participación de egresos sobre rendimiento",
                                                          compute="compute_participacion_egreso_sobre_rendimiento")
    importe_mes_actual = fields.Float(string="Importe mes actual", compute="compute_importe_mes_actual")
    por_participacion_sobre_total2 = fields.Float(string="Porcentaje de participación sobre el total",
                                                  compute="compute_por_participacion_sobre_total2", digits=(16, 4))

    periodo_id = fields.Many2one('pbp.fondo_garantias_periodos', string="Periodo", required=True)

    @api.onchange('importe_mes_anterior')
    @api.depends('importe_mes_anterior')
    def compute_por_participacion_sobre_total(self):
        for i in self:
            porcentaje = 0
            total_mes_anterior = sum(i.periodo_id.fondo_garantia_ids.mapped('importe_mes_anterior'))
            if total_mes_anterior > 0:
                porcentaje = i.importe_mes_anterior/total_mes_anterior
            i.write({'por_participacion_sobre_total': porcentaje})

    @api.onchange('importe_mes_anterior', 'cobro_fg_aporte_cbsa')
    @api.depends('importe_mes_anterior', 'cobro_fg_aporte_cbsa')
    def compute_importe_mes_actual(self):
        for i in self:
            total = (i.importe_mes_anterior + i.cobro_fg_aporte_cbsa + i.participacion_sobre_rendimiento +
                     i.participacion_egreso_sobre_rendimiento)
            i.write({'importe_mes_actual': total})

    @api.onchange('importe_mes_anterior')
    @api.depends('importe_mes_anterior')
    def compute_por_participacion_sobre_total2(self):
        for i in self:
            total_mes_actual = sum(i.periodo_id.fondo_garantia_ids.mapped('importe_mes_actual'))
            if total_mes_actual > 0:
                porcentaje = i.importe_mes_actual / total_mes_actual
                i.write({'por_participacion_sobre_total2': porcentaje})
            else:
                i.write({'por_participacion_sobre_total2': 0})

    @api.onchange('por_participacion_sobre_total','periodo_id.egreso_mes','periodo_id.capital_vencido_mes')
    @api.depends('por_participacion_sobre_total','periodo_id.egreso_mes','periodo_id.capital_vencido_mes')
    def compute_participacion_egreso_sobre_rendimiento(self):
        for i in self:
            total = i.por_participacion_sobre_total*i.periodo_id.egreso_mes+i.periodo_id.capital_vencido_mes
            i.write({'participacion_egreso_sobre_rendimient': total})

    @api.onchange('por_participacion_sobre_total')
    @api.depends('por_participacion_sobre_total')
    def compute_participacion_egreso_sobre_rendimiento(self):
        for i in self:
            total = i.por_participacion_sobre_total * i.periodo_id.rendimiento_mes
            i.write({'participacion_egreso_sobre_rendimiento': total})

    def compute_cobro_fg_aporte_cbsa(self):
        for i in self:
            diario_fg = self.env['account.journal'].search(
                [('diario_fg', '=', True), ('currency_id', '=', i.periodo_id.currency_id.id)])
            if diario_fg:
                lineas = self.env['account.move.line'].search([('account_id', '=', diario_fg.default_account_id),
                                                               ('date', '>=', i.periodo_id.fecha_inicio),
                                                               ('date', '<=', i.periodo_id.fecha_fin),
                                                               ('partner_id','=',i.partner_id.id)])
                i.cobro_fg_aporte_cbsa = sum(lineas.filtered(lambda x: x.amount_currency > 0).mapped('amount_currency'))
            else:
                i.cobro_fg_aporte_cbsa = 0