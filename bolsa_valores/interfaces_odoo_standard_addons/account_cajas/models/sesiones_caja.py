from odoo import fields, api, models, exceptions
from datetime import datetime


class AccountCajaSession(models.Model):
    _name = 'account.caja.session'
    _order = 'id desc'

    name = fields.Char(string="Número", required=True,
                       default='Nuevo', readonly=True)
    statement_ids = fields.Many2many(
        'account.bank.statement', string="Extractos")
    fecha_hora_inicio = fields.Datetime(
        'Fecha/hora inicio', default=datetime.now())
    fecha_hora_fin = fields.Datetime('Fecha/hora fin')
    user_id = fields.Many2one(
        'res.users', string="Cajero", required=True, default=lambda self: self.env.user)
    state = fields.Selection(string="Estado", selection=[('apertura', 'Apertura'), (
        'proceso', 'En proceso'), ('cierre', 'Cierre'), ('done', 'Cerrada y contabilizada')], default='apertura')
    caja_id = fields.Many2one('account.caja', string="Caja", required=True)
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.user.company_id.currency_id)
    st_efectivo = fields.Many2one(
        'account.bank.statement', string="Diario de efectivo", compute="compute_st_efectivo")
    saldo_apertura = fields.Monetary(
        string='Saldo de apertura', related="st_efectivo.balance_start")
    transacciones = fields.Monetary(
        string='Transacciones', related="st_efectivo.total_entry_encoding")
    saldo_teorico_cierre = fields.Monetary(
        string='Saldo teórico de cierre', related="st_efectivo.balance_end")
    saldo_cierre = fields.Monetary(
        string='Saldo cierre', related="st_efectivo.balance_end_real")
    diferencia = fields.Monetary(
        string='Diferencia', related="st_efectivo.difference")
    
    def compute_st_efectivo(self):
        for i in self:
            for j in i.statement_ids:
                if j.journal_id.type == 'cash':
                    i.st_efectivo = j.id

    def open_cashbox_id(self):
        self.ensure_one()
        context = dict(self.env.context or {})
        if context.get('balance'):
            context['statement_id'] = self.st_efectivo.id
            if context['balance'] == 'start':
                cashbox_id = self.st_efectivo.cashbox_start_id.id
            elif context['balance'] == 'close':
                cashbox_id = self.st_efectivo.cashbox_end_id.id
            else:
                cashbox_id = False

            action = {
                'name': 'Control de efectivo',
                'view_mode': 'form',
                'res_model': 'account.bank.statement.cashbox',
                'view_id': self.env.ref('account.view_account_bnk_stmt_cashbox_footer').id,
                'type': 'ir.actions.act_window',
                'res_id': cashbox_id,
                'context': context,
                'target': 'new'
            }

            return action


    def button_iniciar_sesion(self):
        self.write({'state': 'proceso'})

    def button_cerrar_sesion(self):
        if self.env.user == self.user_id or self.env.user.has_group('base.group_system'):
            for i in self.statement_ids:
                if (i != self.st_efectivo) and (i.balance_end != i.balance_end_real):
                    i.write({'balance_end_real': i.balance_end})
            self.write(
                {'state': 'cierre', 'fecha_hora_fin': fields.Datetime.now()})
        else:
            raise exceptions.ValidationError(
                'La sesión está asignada a otro usuario')

    def button_validar(self):
        if self.env.user == self.user_id or self.env.user.has_group('base.group_system'):
            for i in self.statement_ids:
                i.button_post()
                for j in i.line_ids:
                    for x in j.payment_id.move_id.line_ids.filtered(lambda z: z.debit> 0):         
                        line_to_change=j.line_ids.filtered(lambda x:x.credit>0)
                        line_to_change.write({'account_id':x.account_id.id})
                        (x + line_to_change).reconcile()
                i.button_validate_or_action()
            self.write({'state': 'done'})
            return
        else:
            raise exceptions.ValidationError(
                'La sesión está asignada a otro usuario')

    def validar_caja_abierta(self, caja_id):
        duplicada = self.env['account.caja.session'].search(
            [('caja_id', '=', caja_id), ('state', '!=', 'done')])
        if duplicada:
            raise exceptions.ValidationError(
                'Ya existe una sesión abierta para esta caja')
        else:
            return

    def validar_sesion_unica(self, user_id):
        duplicada = self.env['account.caja.session'].search(
            [('user_id', '=', user_id), ('state', '!=', 'done')])
        if duplicada:
            raise exceptions.ValidationError(
                'Ya existe una sesión abierta para este usuario')
        else:
            return

    @api.model
    def create(self, vals):
        caja = vals.get('caja_id')
        self.validar_caja_abierta(caja)
        user = self.env.uid
        self.validar_sesion_unica(user)
        caja = self.env['account.caja'].browse(caja)
        vals['name'] = caja.sudo().sequence_id.next_by_id()
        statements = []
        for i in caja.journal_ids:
            st = {
                'journal_id': i.id,
                'name': vals.get('name'),
                'user_id': self.env.user.id,
                'company_id': self.env.user.company_id.id
            }
            statements.append((0, 0, st))
        vals['statement_ids'] = statements
        return super(AccountCajaSession, self).create(vals)
