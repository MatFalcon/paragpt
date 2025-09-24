from odoo import models, fields, api, exceptions


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

    #def default_name(self):
    #    return self.env['ir.sequence'].sudo().next_by_code('seq_periodo_secuencia_garantias')

    def button_confirmar(self):
        for i in self:
            i.write({'state': 'confirmado'})
        return

    def generar_registros(self):
        for i in self:
            if not i.fecha_inicio or not i.fecha_fin or i.fecha_inicio > i.fecha_fin:
                raise exceptions.ValidationError(
                    'No existe un producto destinado a custodias físicas. Favor verificar')
            else:
                st = self.env['pbp.novedades_series'].search([('fecha','<=',i.fecha_fin),
                                                              ('fecha','>=',i.fecha_inicio),
                                                              ('currency_id','=', i.currency_id.id)])
                novedades = self.env['pbp.novedades'].search([('fecha_operacion','<=',i.fecha_fin),
                                                              ('fecha_operacion','>=',i.fecha_inicio),
                                                              ('currency_id','=', i.currency_id.id)])
                calculos = self.env['pbp.calculo_fondo_garantia'].search([('fecha_operacion','<=',i.fecha_fin),
                                                                          ('fecha_operacion','>=',i.fecha_inicio),
                                                                          ('currency_id','=', i.currency_id.id)])

                partners_st = list(set(st.mapped('partner_id.id')))
                partners_sen = list(set(novedades.mapped('partner_id.id')))
                partners = list(set(partners_st + partners_sen))
                for p in partners:
                    volumen_negociado_renta_fija_st = sum(st.filtered(lambda x:x.partner_id.id == p and x.product_id.tipo_renta == 'fija').mapped('volumen'))
                    volumen_negociado_renta_variable_st = sum(st.filtered(lambda x:x.partner_id.id == p and x.product_id.tipo_renta == 'variable').mapped('volumen'))
                    volumen_negociado_renta_variable_sen = sum(novedades.filtered(lambda x:x.partner_id.id == p and x.product_id.tipo_renta == 'variable').mapped('volumen_gs'))
                    volumen_negociado_renta_fija_sen = sum(novedades.filtered(lambda x:x.partner_id.id == p and x.product_id.tipo_renta == 'fija').mapped('volumen_gs'))
                    fondo_garantia_repo = sum(calculos.filtered(lambda x:x.partner_id.id == p).mapped('calculo'))
                    vals = {
                        'partner_id':p,
                        'volumen_negociado_renta_fija_st':volumen_negociado_renta_fija_st,
                        'volumen_negociado_renta_variable_st':volumen_negociado_renta_variable_st,
                        'volumen_negociado_renta_variable_sen': volumen_negociado_renta_variable_sen,
                        'volumen_negociado_renta_fija_sen':volumen_negociado_renta_fija_sen,
                        'fondo_garantia_repo':fondo_garantia_repo,
                        'currency_id':i.currency_id.id
                    }
                    if p in i.mapped('fondo_garantia_ids.partner_id.id'):
                        r = i.mapped('fondo_garantia_ids').filtered(lambda x:x.partner_id.id == p)
                        r.write({
                            'volumen_negociado_renta_fija_st': volumen_negociado_renta_fija_st,
                            'volumen_negociado_renta_variable_st': volumen_negociado_renta_variable_st,
                            'volumen_negociado_renta_variable_sen': volumen_negociado_renta_variable_sen,
                            'volumen_negociado_renta_fija_sen': volumen_negociado_renta_fija_sen,
                            'fondo_garantia_repo': fondo_garantia_repo,
                            'currency_id': i.currency_id.id
                        })
                    else:
                        i.write({'fondo_garantia_ids':[(0,0,vals)]})


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
    volumen_negociado_renta_fija_st = fields.Float(string="Volumen Negociado Renta Fija | Sistema Tradicional")
    descuentos_varios = fields.Float(string="Descuentos varios (TAN)")
    volumen_negociado_renta_variable_st = fields.Float(string="Volumen Negociado Renta Variable | Sistema Tradicional")
    volumen_negociado_renta_variable_sen = fields.Float(string="Volumen Negociado Renta Variable | SEN")
    volumen_negociado_renta_fija_sen = fields.Float(string="Volumen Negociado Renta Fija | SEN")
    volumen_operado_hacienda = fields.Float(string="Volumen Operado Hacienda | TAN")
    fondo_garantia = fields.Monetary(string="Fondo de Garantia", compute="computeFondoGarantia")
    currency_id = fields.Many2one('res.currency', required=True, string="Moneda")
    fondo_garantia_repo = fields.Monetary(string="Fondo de Garantia Repo")
    suma_fondo_garantia = fields.Float(string="Total Fondo de Garantia Repo", compute="computeFondoGarantia")

    periodo_id = fields.Many2one('pbp.fondo_garantias_periodos', string="Periodo", required=True)

    @api.depends('volumen_negociado_renta_fija_st','volumen_negociado_renta_variable_st','volumen_negociado_renta_fija_sen','volumen_negociado_renta_variable_sen','volumen_operado_hacienda')
    def computeFondoGarantia(self):
        for i in self:
            i.fondo_garantia = ((i.volumen_negociado_renta_fija_st+ i.volumen_negociado_renta_variable_st +
                                 i.volumen_negociado_renta_fija_sen + i.volumen_negociado_renta_variable_sen) * 0.00005)
            i.suma_fondo_garantia = i.fondo_garantia_repo + i.fondo_garantia