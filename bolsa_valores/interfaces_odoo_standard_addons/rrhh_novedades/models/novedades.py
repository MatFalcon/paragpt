from odoo import api, fields, models, exceptions
import datetime

from dateutil.relativedelta import *


class TiposNovedades(models.Model):
    _name = 'hr.novedades.tipo'
    _description = "Tipo de novedad"

    name = fields.Char(string="Nombre")
    requiere_confirmacion = fields.Boolean(string="Require confirmación", default=False)
    periodicidad = fields.Selection(string="Periodicidad",
                                    selection=[("puntual", "Puntual"), ("periodico", "Periodico")], default="puntual",
                                    required=True)
    tipo_cuota = fields.Selection([('monto_fijo', 'Monto Fijo'), ('porcentaje_sobre_bruto', 'Porcentaje Sobre Salario Bruto')], default='monto_fijo',
                                  string="Tipo de Cuota")
    interes = fields.Float(string="Porcentaje de interés")
    # cantidad=fields.Integer(string="Número de entradas",default=1,help="Cantidad de veces que debe generar una Novedad. Ejemplo: Cantidad de cuotas. Ingrese -1 para que se ejecute siempre")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    code = fields.Char(string='Código')
    desembolso = fields.Boolean(string="Desembolsable", default=False)
    account_account_desembolso_id = fields.Many2one('account.account', string='Cuenta para el desembolso')
    tipo_novedad_adelanto_aguinaldo = fields.Boolean(string='Novedad para Adelanto de Aguinaldos', default=False)

    # @api.model_create_multi
    # @api.returns('self', lambda value: value.id)
    # def create(self, vals_list):
    #     return super(TiposNovedades, self).create(vals_list)
    @api.onchange('tipo_novedad_adelanto_aguinaldo')
    def onchange_novedad_adelanto_aguinaldo(self):
        for this in self:
            this.periodicidad = 'puntual'
            this.tipo_cuota = 'monto_fijo'
            this.interes = 0


class Novedades(models.Model):
    _name = 'hr.novedades'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Novedad'

    def default_name(self):
        # rrhh_novedades/models/novedades.py
        return self.env['ir.sequence'].sudo().next_by_code('seq_novedad')

    name = fields.Char(string='Número', default=lambda self: self.default_name())
    tipo_id = fields.Many2one("hr.novedades.tipo", string="Tipo de novedad", ondelete="restrict", tracking=1)
    desembolso = fields.Boolean(string="Desembolsable", related="tipo_id.desembolso")
    periodicidad = fields.Selection(string="Periodicidad", related="tipo_id.periodicidad")
    tipo_cuota = fields.Selection(string="Tipo de Cuota", related='tipo_id.tipo_cuota')
    novedad_original = fields.Many2one('hr.novedades')
    fecha = fields.Date(string='Fecha de Procesamiento', required=True, tracking=1)
    fecha_desembolso = fields.Date(string='Fecha de Desembolso', tracking=1)
    employee_id = fields.Many2one("hr.employee", string='Empleado', required=True, tracking=1)
    contract_id = fields.Many2one("hr.contract", string='Contrato', required=True, tracking=1)
    monto = fields.Float(string="Monto", required=True, default=0, copy=False, tracking=1)
    state = fields.Selection(selection=[
        ("draft", "Borrador"),
        ("done", "Confirmado"),
        ("cancel", "Cancelado"),
        ("procesado", "Procesado"),
    ], string="Estado", default="draft", tracking=1)
    payslip_id = fields.Many2one("hr.payslip", string="Nómina", copy=False)
    comentarios = fields.Char(string="Comentarios", tracking=1)
    fecha_inicio = fields.Date("Fecha de inicio", copy=False, tracking=1)
    cant_cuotas = fields.Integer("Cantidad de cuotas", default=1, copy=False, tracking=1)
    nro_cuota = fields.Integer("Nro. de cuota", copy=False, tracking=1)
    monto_total = fields.Float(string="Monto total", tracking=1)
    monto_objetivo = fields.Float(string="Monto objetivo", copy=False, tracking=1)
    monto_amortizado = fields.Float(string="Monto amortizado", copy=False, tracking=1)
    porcentaje_a_descontar = fields.Integer(string="Porcentaje del Salario Bruto a descontar", tracking=1)
    es_cuota = fields.Boolean(default=False, copy=False, tracking=1)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    readonly_monto = fields.Boolean(compute="compute_readonly_monto")
    desbloquear_monto = fields.Boolean(string="Desbloquear monto", default=False, copy=False, tracking=1)
    amount_to_show = fields.Char(string='Valor', compute='_get_amount_to_show')

    payment_id = fields.Many2one('account.payment', string='Pago')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for this in self:
            contract_id = False
            if this.employee_id and this.employee_id.contract_id and this.employee_id.contract_id.state == 'open':
                contract_id = this.employee_id.contract_id
            if this.contract_id != contract_id:
                this.contract_id = contract_id

    def _get_amount_to_show(self):
        for this in self:
            amount_to_show = 'Monto: ' + (str('{:,.0f}'.format(this.monto))).replace(',', '.')
            if this.periodicidad == 'periodico' and this.tipo_cuota == 'porcentaje_sobre_bruto':
                amount_to_show = str(this.porcentaje_a_descontar) + '% del Salario Bruto' + (
                    (', ' + amount_to_show) if this.state == 'procesado' else '')

            this.amount_to_show = amount_to_show

    def button_desbloquear_monto(self):
        # rrhh_novedades/models/novedades.py
        for i in self:
            i.write({'desbloquear_monto': True})

    @api.depends('state', 'periodicidad', 'desbloquear_monto')
    def compute_readonly_monto(self):
        # rrhh_novedades/models/novedades.py
        for i in self:
            readonly = (i.state != 'draft') or (i.periodicidad == 'periodico' and not i.desbloquear_monto)
            i.readonly_monto = readonly

    def unlink(self):
        # rrhh_novedades/models/novedades.py
        for i in self:
            if i.state != "draft":
                raise exceptions.ValidationError("No se pueden eliminar novedades que no estén en estado Borrador")
        return super(Novedades, self).unlink()

    def generar_cuotas(self, puntual=False):
        # rrhh_novedades/models/novedades.py
        for i in self:
            monto_cuota = i.monto_total / i.cant_cuotas
            if puntual:
                monto_cuota = monto_cuota + (monto_cuota * i.tipo_id.interes / 100)
            else:
                monto_cuota = monto_cuota + ((monto_cuota * i.tipo_id.interes / 100) / 12 * i.cant_cuotas)
            i.write({
                'monto': round(monto_cuota),
                'nro_cuota': 1,
                'comentarios': "Cuota 1 de %s" % i.cant_cuotas,
                'fecha': i.fecha_inicio,
                'es_cuota': True
            })
            if i.periodicidad == 'periodico':
                for k in range(2, i.cant_cuotas + 1):
                    nov = {
                        'tipo_id': i.tipo_id.id,
                        'fecha': i.fecha_inicio + relativedelta(months=+(k - 1)),
                        'monto': round(monto_cuota),
                        'monto_total': i.monto_total,
                        'cant_cuotas': i.cant_cuotas,
                        'nro_cuota': k,
                        'comentarios': "Cuota %s de %s" % (k, i.cant_cuotas),
                        'employee_id': i.employee_id.id,
                        'contract_id': i.contract_id.id,
                        'state': 'done',
                        'fecha_inicio': i.fecha_inicio,
                        'es_cuota': True,
                        'novedad_original': i.id,
                    }
                    self.env['hr.novedades'].create(nov)

    def button_confirmar(self):
        # rrhh_novedades/models/novedades.py
        for i in self:
            cuota_monto_ok = False

            if i.periodicidad == 'periodico' and not i.es_cuota:
                i.generar_cuotas()
                cuota_monto_ok = True
            elif not i.periodicidad == 'periodico' and not i.es_cuota and i.tipo_id.interes > 0:
                i.cant_cuotas = 1
                i.monto_total = i.monto
                i.fecha_inicio = i.fecha
                i.generar_cuotas(puntual=True)
                cuota_monto_ok = True

            # i.write({'state': 'done',
            #         'monto': (i.monto + (i.monto * i.tipo_id.interes / 100) if not cuota_monto_ok else i.monto)})
            i.write({'state': 'done'})

    def button_cancelar(self):
        # rrhh_novedades/models/novedades.py
        for i in self:
            if i.state in ['procesado']:
                raise exceptions.ValidationError("No se puede cancelar una novedad en estado Procesado")
            elif i.payment_id:
                raise exceptions.ValidationError("No se puede cancelar una novedad que ya se ha desembolsado, elimine el pago antes de continuar")
            else:
                i.write({'state': 'cancel'})
        return

    def button_draft(self):
        # rrhh_novedades/models/novedades.py
        for i in self:
            if i.state not in ['cancel']:
                raise exceptions.ValidationError("Sólo se puede cambiar a borrador registros en estado cancelado")
            else:
                i.write({'state': 'draft'})
        return

    def action_process(self, payslip):
        for this in self:
            if this.periodicidad == 'periodico' and this.tipo_cuota == 'porcentaje_sobre_bruto':
                monto_descontado = sum(payslip.line_ids.filtered(lambda x: x.category_id.code in ['GROSS']).mapped('total')) / 100 * this.porcentaje_a_descontar
                tope_novedad = this.monto_objetivo - this.monto_amortizado
                if monto_descontado > tope_novedad:
                    monto_descontado = tope_novedad
                this.write({
                    'monto': monto_descontado,
                })
                monto_saldo = this.monto_objetivo - this.monto_amortizado - this.monto
                if monto_saldo > 0:
                    next_fecha = this.fecha + datetime.timedelta(days=1)
                    while next_fecha.day != this.fecha.day:
                        next_fecha += datetime.timedelta(days=1)

                    next_novedad = this.copy()
                    next_novedad.write({
                        'novedad_original': this.id,
                        'fecha': next_fecha,
                        'monto_objetivo': this.monto_objetivo,
                        'monto_amortizado': this.monto_amortizado + this.monto,
                        'fecha_inicio': this.fecha_inicio,
                        'nro_cuota': this.nro_cuota + 1,
                        'state': 'done',
                    })

            self.write({'payslip_id': payslip.id, 'state': 'procesado'})

    def action_not_process(self):
        for this in self:
            if this.periodicidad == 'periodico' and this.tipo_cuota == 'porcentaje_sobre_bruto':
                next_novedades = self.search([('novedad_original', '=', this.id)])
                for next_novedad in next_novedades:
                    if next_novedad.state == 'procesado':
                        raise exceptions.ValidationError(
                            "No es posible cancelar esta nómina. \nAl confirmar esta nómina, una novedad de tipo Porcentaje sobre el Salario Bruto se marcó como procesada y se creó otra novedad del mismo tipo para el saldo restante de la misma, se deben de cancelar todas las nóminas confirmadas siguientes a esta para marcar sus novedades como pendientes."
                        )
                    next_novedad.action_not_process()
                    next_novedad.button_cancelar()
                    next_novedad.button_draft()
                    next_novedad.unlink()
                this.write({
                    'monto': 0,
                })
        self.write({
            'state': 'done',
        })

    def button_create_account_payment(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Desembolso',
            'res_model': 'hr.novedades.desembolso_wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_novedades_ids': self.filtered(lambda x: x.tipo_id.desembolso and x.state in ['done', 'procesado'] and not x.payment_id).ids},
        }

    def action_show_account_payment(self):
        if self.payment_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Detalle del Pago',
                'res_model': 'account.payment',
                'res_id': self.payment_id.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
                'context': self.env.context,
            }
        else:
            # Manejar la situación donde no hay un pago asociado
            return {}


class HRNovedadesDesembolsoWizard(models.TransientModel):
    _name = 'hr.novedades.desembolso_wizard'
    _description = 'Wizard para desembolso de Novedades'

    novedades_ids = fields.Many2many('hr.novedades', string='Novedades', required=True)
    account_journal_id = fields.Many2one('account.journal', string='Diario', required=True)
    confirm_payment = fields.Boolean(string='Confirmar Pagos', default=False)

    def button_create_account_payment(self):
        for novedad in self.novedades_ids.filtered(lambda x: x.tipo_id.desembolso and x.state in ['done', 'procesado'] and not x.payment_id):
            if not novedad.contract_id.employee_id.address_home_id:
                raise exceptions.ValidationError(
                    "El empleado " + novedad.contract_id.employee_id.name + " no tiene asignado un contacto, primero debe de asignarle un contacto antes de poder crear un pago"
                )
            payment_amount = 0
            if novedad.periodicidad == 'puntual':
                payment_amount = novedad.monto
            elif novedad.periodicidad == 'periodico':
                payment_amount = novedad.monto_total

            payment = novedad.payment_id.sudo().create({
                'payment_type': 'outbound',
                'partner_id': novedad.contract_id.employee_id.address_home_id.id,
                'journal_id': self.account_journal_id.id,
                'destination_account_id': novedad.tipo_id.account_account_desembolso_id.id,
                'date': novedad.fecha_desembolso,
                'amount': payment_amount,
                'ref': novedad.name,
            })
            novedad.payment_id = payment.id
            if self.confirm_payment:
                payment.sudo().action_post()
