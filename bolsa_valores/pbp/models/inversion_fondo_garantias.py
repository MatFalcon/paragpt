import datetime

from odoo import models, fields, api, exceptions

from odoo.addons.pbp.facturas.asientos import generar_asientos
from datetime import date, datetime, timedelta


class InversionFondoGarantias(models.Model):
    _name = 'pbp.inversion_fondo_garantias'
    _order = 'state, fecha_compra desc'
    _rec_name = 'id'

    emision = fields.Char(string='Emisión')
    serie = fields.Char(string="Serie", required=True)
    fecha_actual = fields.Date(string="Fecha")
    fecha_compra = fields.Date(string='Fecha de Compra')
    fecha_vencimiento = fields.Date(string='Fecha de Vencimiento', required=False)
    calificacion_riesgo = fields.Char(string='Calificación Riesgo')
    tasa_interes = fields.Float(string='Tasa Interés', digits=(7, 6))
    importe_valorizado = fields.Float(digits=(17, 6), required=True)
    #valor_actual_pyg = fields.Float(string='Valor Actual en PYG', digits=(17, 6))
    valor_actual_usd = fields.Float(string='Valor Actual en USD', digits=(17, 6))
    amortizacion = fields.Float(string='Amortización', digits=(17, 6))
    #estado_de_cupon = fields.Char(string='Estado de Cupón / Capital')
    comitente = fields.Integer()
    #capital = fields.Float(string="Capital")
    #intereses = fields.Float(digits=(17, 6), string="Intereses")
    #valor_calculado = fields.Monetary(store=True, string='Total')

    tipo = fields.Selection(
        selection=[
            ('intereses', 'Intereses'),
            ('capital', 'Capital'),
        ], required=True
    )

    #grupo_id = fields.Many2one('pbp.grupo_cartera_inversion')

    instrumento = fields.Selection(
        selection=[
            ('acciones', 'Acciones'),
            ('bonos', 'Bonos'),
            ('bonos_cartulares', 'Bonos Cartulares'),
            ('bonos_corporativos', 'Bonos Corporativos'),
            ('bonos_del_tesoro', 'Bonos del Tesoro'),
            ('bonos_financieros', 'Bonos Financieros'),
            ('bonos_subordinados', 'Bonos Subordinados'),
            ('cda', 'CDA'),
            ('fondos', 'Fondos'),
        ],
    )

    state = fields.Selection(
        selection=[
            ('acreditado', 'Acreditado'),
            ('pendiente', 'Pendiente')
        ],
        required=True,
        default='pendiente',
        string='Estado',
    )

    partner_id = fields.Many2one('res.partner', string='Emisor', required=True)
    casa_bolsa = fields.Many2one('res.partner', string='Casa de Bolsa', required=True)
    #credit_account_id = fields.Many2one('account.account', string='Acreedor', required=False)
    #initial_credit_account_id = fields.Many2one('account.account', string='Acreedor Inicial', required=False)
    #initial_debit_account_id = fields.Many2one('account.account', string='Deudor Inicial', required=False)
    #debit_account_id = fields.Many2one('account.account', string='Deudor', required=False)
    currency_id = fields.Many2one('res.currency', string="Moneda", required=True)
    #move_id = fields.Many2one('account.move', string="Asiento", copy=False)
    #initial_move_id = fields.Many2one('account.move', string="Asiento Inicial", copy=False)
    tipo_cambio = fields.Float(string='Tipo de Cambio del día')

    def getTipoCambioDia(self):
        registros = self.env['pbp.inversion_fondo_garantias'].search([('currency_id.name', '=', 'PYG')])
        PYG = self.env['res.currency'].search([('name', '=', 'PYG')])
        USD = self.env['res.currency'].search([('name', '=', 'USD')])
        for r in registros:
            valor_actual_usd = PYG._convert_tipo_cambio_comprador(r.importe_valorizado, USD, self.env.company,
                                                                   date.today())
            r.write({'valor_actual_usd':valor_actual_usd})

    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        for val in vals_list:
            if val['importe_valorizado'] <= 0:
                raise exceptions.UserError("No se puede crear el registro. El Importe valorizado debe ser mayor a 0")
            elif val['currency_id'] == 2:
                val['valor_actual_usd'] = val['importe_valorizado']
        recs = super(InversionFondoGarantias, self).create(vals_list)
        #for r in recs:
        #    r.generarAsientoInicial()
        return recs

    """def generarAsientoInicial(self):
        for cartera in self:
            liquidity_balance = cartera.importe_valorizado
            line_ids = []
            debit_line = {
                'debit': liquidity_balance,
                'credit': 0.0,
                'account_id': cartera.initial_debit_account_id.id,
                'partner_id': cartera.casa_bolsa.id,
                'currency_id': cartera.currency_id.id,
                'amount_currency': liquidity_balance,
            }
            line_ids.append((0, 0, debit_line))

            credit_line = {
                'credit': liquidity_balance,
                'debit': 0.0,
                'account_id': cartera.initial_credit_account_id.id,
                'partner_id': cartera.casa_bolsa.id,
                'currency_id': cartera.currency_id.id,
                'amount_currency': -liquidity_balance,
            }
            line_ids.append((0, 0, credit_line))
            move = {
                'ref': cartera.serie,
                'date': date.today(),
                'currency_id': cartera.currency_id.id,
                'move_type': 'entry',
            }
            move = self.env['account.move'].with_context(check_move_validity=False).create([move])
            move.write({'line_ids': line_ids})
            move.action_post()
            cartera.write({'initial_move_id': move.id})"""
    
    """"@api.depends('valor_actual_pyg', 'fecha_actual')
    def compute_valor_final(self):
        for cartera in self:
            if cartera.currency_id.name == 'USD' and cartera.valor_actual_pyg and cartera.fecha_actual:
                cartera.valor_calculado = 0.0
                PYG = self.env['res.currency'].search([('name', '=', 'PYG')])
                USD = self.env['res.currency'].search([('name', '=', 'USD')])
                cartera.valor_calculado = PYG._convert_tipo_cambio_comprador(cartera.valor_actual_pyg, USD, self.env.company,
                                                       cartera.fecha_actual)
            elif cartera.valor_actual_pyg:
                cartera.valor_calculado = cartera.valor_actual_pyg
            else:
                cartera.valor_calculado = 0"""

    @api.model
    def get_last_date_of_month(self, year, month):
        if month == 12:
            last_date = datetime(year, month, 31)
        else:
            last_date = datetime(year, month + 1, 1) + timedelta(days=-1)

        return last_date.strftime("%Y-%m-%d")

    """@api.onchange('fecha_vencimiento')
    def onchangeFechaVencimiento(self):
        for i in self:
            if i.fecha_vencimiento:
                i.fecha_actual = i.get_last_date_of_month(i.fecha_vencimiento.year, i.fecha_vencimiento.month)
            else:
                i.fecha_actual = False"""

    """@api.onchange('tipo', 'instrumento', 'fecha_vencimiento', 'currency_id')
    def set_credit_debit_accounts(self):
        for cartera in self:
            credit_accounts = self.env['account.account'].search([
                ('cartera_acreedor_deudor', '=', 'acreedor'),
                ('cartera_tipo', '=', cartera.tipo),
            ])
            cartera.credit_account_id = credit_accounts[0] if credit_accounts else False

            vencimiento = False
            ten_years = date.today().year + 10
            if cartera.fecha_vencimiento and cartera.fecha_vencimiento.year > ten_years:
                vencimiento = 'largo_plazo'
            elif cartera.fecha_vencimiento:
                vencimiento = 'corto_plazo'

            debit_accounts = self.env['account.account'].search([('cartera_acreedor_deudor', '=', 'deudor')]).filtered(lambda account:
                (account.cartera_vencimiento == vencimiento or not account.cartera_vencimiento) and
                (account.cartera_instrumento == cartera.instrumento or not account.cartera_instrumento) and
                (account.cartera_tipo == cartera.tipo or not account.cartera_tipo) and
                (account.cartera_currency_id == cartera.currency_id or not account.cartera_currency_id)
            )
            cartera.debit_account_id = debit_accounts[0] if debit_accounts else False"""

    def marcar_como_inactivo(self):
        self.state = 'inactivo'
        dialog = self.env['pbp.dialog.box'].sudo().search([])[-1]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Message',
            'res_model': 'pbp.dialog.box',
            'view_mode': 'form',
            'target': 'new',
            'res_id': dialog.id
        }

    """def generar_asientos(self, records=None):
        if records:
            carteras = records.read((set(self.env['pbp.inversion_fondo_garantias']._fields)))
            carteras = [cartera for cartera in carteras]
        else:
            carteras = self.env['pbp.cartera_inversion'].search_read([
                ['state', '=', 'pendiente'],
                # ['fecha_compra', '>=', from_date],
                # ['fecha_compra', '<=', to_date],
            ])

        data = generar_asientos(self.env, carteras)
        dialog = self.env['pbp.dialog.box'].sudo().create({
            'cartera_inversion_publicadas_ids': data['cartera_inversion_publicadas_ids'],
            'cartera_inversion_fallidas_ids': data['cartera_inversion_fallidas_ids'],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Message',
            'res_model': 'pbp.dialog.box',
            'view_mode': 'form',
            'target': 'new',
            'res_id': dialog.id
        }"""

    """@api.model
    def generarAsientosVencimiento(self):
        fecha_actual = date.today()
        carteras_vencidas = self.env['pbp.inversion_fondo_garantias'].search([('fecha_vencimiento', '=', fecha_actual),
                                                                      ('credit_account_id', '!=', False),
                                                                      ('debit_account_id', '!=', False),
                                                                      ('move_id', '=', False)])
        if carteras_vencidas:
            carteras = carteras_vencidas.read((set(self.env['pbp.inversion_fondo_garantias']._fields)))
            carteras = [cartera for cartera in carteras]
            generar_asientos(self.env, carteras)

            carteras_vencidas.mapped('move_id').action_post()"""
