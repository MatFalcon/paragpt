# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date, timedelta
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class CarteraInversion(models.Model):
    _inherit = 'pbp.cartera_inversion'

    # — Campos BVAPY —
    #referencia_tasa        = fields.Char(string="Referencia Tasa")
    #total_general          = fields.Float(string="Total")


    #valor_cuota_inicial     = fields.Float(
    #    string="Valor Cuota Inicial",
    #    help="Valor de la cuota al inicio")
    #fecha_valor_cuota       = fields.Date(
    #    string="Fecha Valor Cuota Inicial")

    # Relaciones One2many
    movimiento_fondo_ids = fields.One2many(
        'pbp.movimiento_fondo', 'cartera_id',
        string="Movimientos de Fondo")
    fondo_periodo_ids = fields.One2many(
        'pbp.vencimiento_fondo_periodo', 'cartera_id',
       string="Períodos de Rendimiento")

# — Períodos de Rendimiento de Fondo —
class VencimientoFondoPeriodo(models.Model):
    _name = 'pbp.vencimiento_fondo_periodo'
    _description = "Períodos de Rendimiento de Fondo"
    _order = 'fecha_inicio desc'

    name = fields.Char(string="Nombre", compute='_compute_name')
    cartera_id   = fields.Many2one(
        'pbp.cartera_inversion',
        string="Cartera",
        required=True,
        ondelete='cascade')
    fecha_inicio = fields.Date(string="Inicio Período", required=True)
    fecha_fin    = fields.Date(string="Fin Período", required=True)
    state        = fields.Selection([
                      ('activo',   'Activo'),
                      ('cerrado', 'Cerrado'),
                  ], default='activo', string="Estado")
    vencimiento_ids = fields.One2many(
        'pbp.vencimiento_fondo', 'periodo_id',
        string="Rendimientos Mensuales")

    acumulado = fields.Float(
        string="Acumulado",
        compute='_compute_acumulado')
    currency_id = fields.Many2one('res.currency', string="Moneda", related="cartera_id.currency_id")

    @api.depends('fecha_inicio', 'fecha_fin')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.cartera_id.serie} - {rec.fecha_inicio} - {rec.fecha_fin}"

    @api.depends('vencimiento_ids')
    def _compute_acumulado(self):
        for rec in self:
            rec.acumulado = sum(rec.vencimiento_ids.mapped('monto_rendimiento'))
    
    def crear_vencimiento(self):
        """
            Crea vencimientos mensuales al final de cada mes dentro del periodo
        """
        fecha_actual = self.fecha_inicio
        while fecha_actual <= self.fecha_fin:
            # Obtener el ultimo dia del mes actual
            ultimo_dia_del_mes = fecha_actual.replace(day=1) + relativedelta(months=1, days=-1)
            if ultimo_dia_del_mes > self.fecha_fin:
                ultimo_dia_del_mes = self.fecha_fin

            # Crear un nuevo vencimiento para el ultimo dia del mes
            self.env['pbp.vencimiento_fondo'].create({
                'periodo_id': self.id,
                'fecha': ultimo_dia_del_mes,
                'monto_rendimiento': 0.0,  # Inicializar con 0 o el valor que corresponda
                'tasa_mensual': 0.0,       # Inicializar con 0 o el valor que corresponda
                'state': 'pendiente'
            })

            # Avanzar al siguiente mes
            fecha_actual = ultimo_dia_del_mes + relativedelta(days=1)

    def action_open_asientos_contables(self):
        """
            Abre el formulario de asientos contables, con el dominio filtrado por el vencimiento de fondo
        """
        account_move_ids = []
        # itera los vencimientos de fondo y agrega los ids de los asientos contables a la lista
        for vencimiento in self.vencimiento_ids:
            if vencimiento.account_move_id:
                account_move_ids.append(vencimiento.account_move_id.id)

        tree_view_id = self.env.ref('account.view_move_tree').id
        form_view_id = self.env.ref('account.view_move_form').id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Asientos Mensuales de Devengamiento',
            'res_model': 'account.move',
            'view_mode': 'tree,form',  # Vista en lista y formulario
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],  # Prioridad tree, alternativo form
            'domain': [('id', 'in', account_move_ids)],  # Filtrar los asientos relacionados
            'context': self.env.context,
        }

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', account_move_ids)],
        }

class AccountMove(models.Model):
    _inherit = 'account.move'

    vencimiento_fondo_id = fields.Many2one(
        'pbp.vencimiento_fondo',
        string="Vencimiento de Fondo")

class VencimientoFondo(models.Model):
    _name = 'pbp.vencimiento_fondo'
    _description = "Rendimiento Mensual de Fondo"


    name = fields.Char(string="Nombre", compute='_compute_name')
    periodo_id        = fields.Many2one(
        'pbp.vencimiento_fondo_periodo',
        string="Período",
        required=True,
        ondelete='cascade')
    fecha             = fields.Date(string="Fecha Cierre", required=True)
    currency_id = fields.Many2one('res.currency', string="Moneda", related='periodo_id.currency_id')
    monto_rendimiento = fields.Float(string="Saldo / Aporte")
    tasa_mensual      = fields.Float(string="Tasa Rendimiento", digits=(7,2))
    entidad           = fields.Many2one('res.partner', string="Entidad (Fondo)")
    state             = fields.Selection([
                          ('pendiente',  'Pendiente'),
                          ('registrado', 'Registrado'),
                      ], default='pendiente',
                      readonly=True)
    acumulado         = fields.Float(
        string="Acumulado",
        compute='_compute_acumulado')

    account_move_id = fields.Many2one(
        'account.move',
        string="Asiento Contable")

    @api.depends('fecha')
    def _compute_name(self):
        for rec in self:
            rec.name = f"{rec.periodo_id.cartera_id.serie} - {rec.fecha}"

    @api.depends('monto_rendimiento', 'state')
    def _compute_acumulado(self):
        for rec in self:
            # Obtener todos los registros del mismo periodo y estado registrado, ordenados por fecha
            lines = self.search([
                ('periodo_id.cartera_id', '=', rec.periodo_id.cartera_id.id),
                ('state', '=', 'registrado')
            ], order='fecha')

            # Calcular el acumulado progresivo
            acumulado = 0.0
            for line in lines:
                acumulado += line.monto_rendimiento
                if line.id == rec.id:
                    rec.acumulado = acumulado
                    break
            else:
                rec.acumulado = 0.0


    def generar_asientos_devengamiento_fondo(self):
        company_currency = self.env.company.currency_id.id
        for record in self:
            if record.monto_rendimiento <= 0:
                raise UserError(_("El monto de rendimiento debe ser positivo."))

            fondo_currency = record.periodo_id.cartera_id.currency_id.id
            # Si la moneda del fondo no es pyg, hay que convertirla
            if fondo_currency != company_currency:
                foreign_amount = record.monto_rendimiento
                company_amount = foreign_amount * record.periodo_id.cartera_id.cambio_utilizado
            else:
                company_amount = record.monto_rendimiento
                foreign_amount = 0.0

            # lineas para el asiento
            debit_line = {
                'account_id': record.periodo_id.cartera_id.inversion_account_id.id,
                'debit': company_amount,
                'credit': 0.0,
                'name': f"{record.fecha} – {record.periodo_id.cartera_id.serie}",
            }
            credit_line = {
                'account_id': record.periodo_id.cartera_id.credit_account_id.id,
                'debit': 0.0,
                'credit': company_amount,
                'name': f"{record.fecha} – {record.periodo_id.cartera_id.serie}",
            }

            
            if fondo_currency != company_currency:
                debit_line.update({
                    'currency_id': fondo_currency,
                    'amount_currency': foreign_amount,
                })
                credit_line.update({
                    'currency_id': fondo_currency,
                    'amount_currency': -foreign_amount,
                })

            lines = [(0, 0, debit_line), (0, 0, credit_line)]

            move_vals = {
                'journal_id': record.periodo_id.cartera_id.inversion_journal_id.id,
                'date':       record.fecha,
                'ref':        record.name,
                'line_ids':   lines,
            }
            if fondo_currency != company_currency:
                move_vals['currency_id'] = fondo_currency

            # Creo el asiento
            move = self.env['account.move'].create(move_vals)
            record.account_move_id = move

            # Marco el vencimiento como registrado
            if record.state == 'pendiente':
                record.state = 'registrado'


class MovimientoFondo(models.Model):
    _name = 'pbp.movimiento_fondo'
    _description = "Movimiento de Capital en Fondo"

    cartera_id = fields.Many2one(
        'pbp.cartera_inversion',
        string="Cartera",
        required=True,
        ondelete='cascade')
    fecha        = fields.Date(
        string="Fecha Movimiento",
        required=True,
        default=date.today())
    tipo         = fields.Selection([
                      ('retiro',        'Retiro'),
                      ('capitalizacion','Capitalización'),
                  ], required=True)
    monto        = fields.Float(string="Monto")

    voucher_id = fields.Many2one(
        'account.voucher',
        string="Voucher")

    def abrir_formulario_voucher(self):
        """Abre el formulario de account.voucher, siempre en guaraníes."""
        company_currency = self.env.company.currency_id.id  # normalmente 155 = PYG
        for rec in self:
            # Validaciones
            if not rec.cartera_id.inversion_journal_id:
                raise UserError(_("Debe completar la Cuenta de Inversión."))
            if not rec.cartera_id.banco_account_id:
                raise UserError(_("Debe completar la Cuenta de Banco."))
            # calcular el importe en PYG
            amt = rec.monto
            if rec.cartera_id.currency_id.id != company_currency:
                # convertir USD  PYG
                amt = amt * rec.cartera_id.cambio_utilizado

            # linea del voucher
            voucher_line_vals = {
                'account_id': rec.cartera_id.inversion_account_id.id,
                'name':       rec.cartera_id.serie or _("N/A"),
                'quantity':   1,
                'price_unit': amt,  # ya en PYG
            }

            # voucher en borrador
            voucher_vals = {
                'voucher_type': 'purchase',
                'partner_id':   rec.cartera_id.partner_id.id,
                'date':         date.today(),
                'journal_id':   rec.cartera_id.inversion_journal_id.id,
                'account_id':   rec.cartera_id.banco_account_id.id,
                'line_ids':     [(0, 0, voucher_line_vals)],
                'state':        'draft',
                'name':         f"{rec.tipo} – {rec.cartera_id.serie or ''}",
            }
            voucher = self.env['account.voucher'].create(voucher_vals)
            rec.voucher_id = voucher.id