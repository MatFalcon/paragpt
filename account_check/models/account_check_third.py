# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __odoo__.py file in module root
# directory
##############################################################################
from odoo import fields, models, _, api,exceptions
import logging
import odoo.addons.decimal_precision as dp
_logger = logging.getLogger(__name__)


class account_check(models.Model):

    _name = 'account.check.third'
    _description = 'Account Check Third'
    _order = "id desc"
    _inherit = ['mail.thread']



    name = fields.Char(
        compute='_get_name',
        string=_('Número'),
        store=True
        )
    number = fields.Integer(
        _('Numero'),
        required=True,
        copy=False
        )
    amount = fields.Float(
        'Monto',
        required=True,
        digits=dp.get_precision('Account'),
        )
    company_currency_amount = fields.Float(
        'Company Currency Amount',
        digits=dp.get_precision('Account'),
        help='This value is only set for those checks that has a different '
        'currency than the company one.'
        )
    voucher_id = fields.Many2one(
        'account.payment',
        'Pago',
        ondelete='set null',
        )
    recibo = fields.Char(string="Nro. de recibo")
    issue_date = fields.Date(
        'Fecha de Emision',
        required=False,
        default=fields.Date.context_today,
        )
    payment_date = fields.Date(
        'Fecha de pago',
        help="Only if this check is post dated"
        )
    destiny_partner_id = fields.Many2one(
        'res.partner',
        compute='_get_destiny_partner',
        string='Destino',
        store=True,
        )
    current_number = fields.Integer(string="Ultimo numero utilizado",readonly=True)
    user_id = fields.Many2one(
        'res.users',
        'Usario',
        default=lambda self: self.env.user,
        )
    payment_amount = fields.Float('Monto de la orden de pago:',compute='_compute_amount')
    retencion_amount = fields.Float('Monto de las retenciones:',compute='_compute_retenciones')
    facturas_asociadas = fields.One2many(string="Facturas asociadas",compute='_compute_facturas')
    clearing = fields.Selection([
            ('24', '24 hs'),
            ('48', '48 hs'),
            ('72', '72 hs'),
        ],
        'Clearing',
        readonly=True,
        states={'handed': [('readonly', False)]})
    state = fields.Selection([
            ('handed', 'En mano'),
            ('deposited', 'Depositado'),
            ('conciliado', 'Conciliado'),
            ('rechazado','Rechazado'),
            ('cancel', 'Anulado'),
        ],
        'State',
        required=True,
        track_visibility='onchange',
        default='handed',
        copy=False,
        )
    supplier_reject_debit_note_id = fields.Many2one(
        'account.move',
        'Supplier Reject Debit Note',
        readonly=True,
        copy=False,
        )
    expense_account_move_id = fields.Many2one(
        'account.move',
        'Expense Account Move',
        readonly=True,
        copy=False,
        )
    replacing_check_id = fields.Many2one(
        'account.check',
        'Replacing Check',
        readonly=True,
        copy=False,
        )

    # Related fields
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        string='Company',
        )
    debit_account_move_id = fields.Many2one(
        'account.move',
        'Asiento contable de débito',
        readonly=True,
        copy=False,
        )
    # Third check
    third_handed_voucher_id = fields.Many2one(
        'account.payment', 'Handed Voucher', readonly=True,)
    source_partner_id = fields.Many2one(
        'res.partner',
        string='Cliente'
        )
    customer_reject_debit_note_id = fields.Many2one(
        'account.move',
        'Customer Reject Debit Note',
        readonly=True,
        copy=False
        )
    bank_id = fields.Many2one(
        'res.bank', 'Banco',
        required=True,
        )
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda'
        )
    vat = fields.Char(
        # TODO rename to Owner VAT
        'Owner Vat',
        )
    owner_name = fields.Char(
        'Propietario',
        )
    deposit_account_move_id = fields.Many2one(
        'account.move',
        'Asiento contable de depósito',
        readonly=True,
        copy=False
        )
    # account move of return
    return_account_move_id = fields.Many2one(
        'account.move',
        'Return Account Move',
        readonly=True,
        copy=False
        )
    asiento_rechazo = fields.Many2one(
        'account.move',
        string="Asiento de rechazo",
        copy = False
    )

    type = fields.Selection([('third_check', 'Cheque de Terceros'), ('issue_check', 'Cheques Propios')],
                            compute='obtener_tipo', string='Tipo')
    journal_id = fields.Many2one('account.journal', compute='obtener_tipo', string='Diario')

    cuenta_origen = fields.Many2one('account.account', string="Cuenta", compute="_obtener_cuenta", store=True)
    tipo_cheque = fields.Selection(selection=[('diferido', 'Diferido'), ('vista', 'Vista')], string="Tipo de Cheque",
                                   compute="definir_tipo_cheque", store=True, tracking=True)
    cuenta_importacion = fields.Many2one('account.account',string="Cuenta contable importada",help="Este campo solo se utiliza en caso de importar cheques vía planilla electrónica u otro medio")

    


    """ _constraints = [
        (_check_number_issue,
            'Check Number must be unique per Checkbook!',
            ['number', 'checkbook_id', 'type']),
        (_check_number_third,
            'Check Number must be unique per Owner and Bank!',
            ['number', 'bank_id', 'owner_name', 'type']),
    ]"""

    @api.depends('voucher_id', 'voucher_id.state')
    def obtener_tipo(self):
        for rec in self:
            if rec.voucher_id:
                rec.type = rec.voucher_id.journal_id.payment_subtype
                rec.journal_id = rec.voucher_id.journal_id.id
            else:
                rec.type = False
                rec.journal_id = False

    @api.depends('voucher_id','cuenta_importacion')
    def _obtener_cuenta(self):
        for rec in self:
            if rec.voucher_id:
                rec.cuenta_origen = rec.voucher_id.journal_id.default_account_id
            elif rec.cuenta_importacion:
                rec.cuenta_origen = rec.cuenta_importacion

    @api.depends('number')
    def _get_name(self):
        self.name = self.number

    @api.depends(
        'voucher_id',
        'voucher_id.partner_id',
        'type',
        'third_handed_voucher_id',
        'third_handed_voucher_id.partner_id',
    )
    def _get_destiny_partner(self):
        partner_id = False
        if self.type == 'third_check' and self.third_handed_voucher_id:
            partner_id = self.third_handed_voucher_id.partner_id.id
        elif self.type == 'issue_check':
            partner_id = self.voucher_id.partner_id.id
        self.destiny_partner_id = partner_id

    @api.depends(
        'voucher_id',
        'voucher_id.partner_id',
        'type',
    )
    def _get_source_partner(self):
        partner_id = False
        if self.type == 'third_check':
            if self.voucher_id:
                partner_id = self.voucher_id.partner_id.id
        self.source_partner_id = partner_id

    @api.depends('number')
    def _get_name(self):
        for rec in self:
            rec.name = rec.number

    @api.depends(
        'voucher_id',
        'voucher_id.partner_id',
        'type',
        'third_handed_voucher_id',
        'third_handed_voucher_id.partner_id',
    )
    def _get_destiny_partner(self):
        for rec in self:
            partner_id = False
            if rec.type == 'third_check' and rec.third_handed_voucher_id:
                partner_id = rec.third_handed_voucher_id.partner_id.id
            elif rec.type == 'issue_check':
                partner_id = rec.voucher_id.partner_id.id
            rec.destiny_partner_id = partner_id

    @api.depends(
        'voucher_id',
        'voucher_id.partner_id',
        'type',
    )
    def _get_source_partner(self):
        partner_id = False
        if self.type == 'third_check':
            partner_id = self.voucher_id.partner_id.id
        self.source_partner_id = partner_id




    @api.depends('issue_date','payment_date')
    def definir_tipo_cheque(self):
        for rec in self:
            if rec.issue_date and rec.payment_date:
                if rec.issue_date == rec.payment_date:
                    rec.tipo_cheque = 'vista'
                else:
                    rec.tipo_cheque = 'diferido'


    @api.depends('voucher_id')
    def _compute_amount(self):
        for rec in self:
            rec.payment_amount = rec.voucher_id.amount






    @api.onchange('issue_date', 'payment_date')
    def onchange_date(self):
        if self.issue_date and self.payment_date:
            if self.issue_date > self.payment_date:
                self.payment_date = False
                raise ValidationError(
                    _('La Fecha de Pago debe Ser mayor o igual que la fecha de emision'))

    @api.onchange('voucher_id')
    def onchange_voucher(self):
        self.vat = self.voucher_id.partner_id.vat


    def unlink(self):
        for rec in self:
            if rec.state not in ('handed','cancel'):
                raise ValidationError(
                _('El cheque debe estar en estado en mano para poder eliminarse'))
        return super(account_check, self).unlink()




    def action_cancel_handed(self):
        for rec in self:
            # go from canceled state to handed state
            rec.write({'state': 'handed'})
            rec.delete_workflow()
            rec.create_workflow()
            return True


    def action_hold(self):
        for rec in self:
            rec.write({'state': 'holding'})
            return True


    def action_deposit(self):
        for rec in self:
            rec.write({'state': 'deposited'})
            return True


    def action_return(self):
        for rec in self:
            rec.write({'state': 'returned'})
            return True


    def action_change(self):
        for rec in self:
            rec.write({'state': 'changed'})
            return True


    def action_hand(self):
        for rec in self:
            existe_credito = False
            facturas = rec.voucher_id.fac_ids
            for factura in facturas:
                if factura.tipo_factura == 2:
                    existe_credito = True
            if existe_credito == True:
                if not rec.recibo:
                    raise ValidationError(('Debe cargarse un numero de recibo para dar como entregado el cheque'))
                else:
                    rec.write({'state': 'handed'})
            else:
                    rec.write({'state': 'handed'})

    def action_handed(self):
        for rec in self:
            rec.state = 'handed'

    def action_validado(self):
        for rec in self:
            rec.state = 'validado'

    def action_sign(self):
        for rec in self:
            rec.state = 'signed'

    def action_handed_signed(self):
        for rec in self:
            rec.state = 'signed'

    def action_signed_validado(self):
        for rec in self:
            rec.state = 'validado'


    def action_validado_handed(self):
        for rec in self:
            rec.state = 'handed'

    def action_reject(self):
        for rec in self:
            rec.write({'state': 'rejected'})
            return True

    def action_conciliar(self):
        for rec in self:
            rec.write({'state': 'conciliado'})
            return True

    def action_rechazar(self):

        return {
            'name': _('Rechazar cheque                                                           '),
            'type': 'ir.actions.act_window',
            'res_model': 'action.rechazo.cheque.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_check_id': self.id,'default_journal_id':self.journal_id.id},
        }


    def action_cancel_rejection(self):
        for check in self:
            if check.customer_reject_debit_note_id:
                raise ValidationError(_(
                    'To cancel a rejection you must first delete the customer '
                    'reject debit note!'))
            if check.supplier_reject_debit_note_id:
                raise ValidationError(_(
                    'To cancel a rejection you must first delete the supplier '
                    'reject debit note!'))
            if check.expense_account_move_id:
                raise ValidationError(_(
                    'To cancel a rejection you must first delete Expense '
                    'Account Move!'))
            check.signal_workflow('cancel_rejection')
        return True

    def action_cancel_debit(self):
        for check in self:
            if check.debit_account_move_id:
                raise ValidationError(_(
                    'To cancel a debit you must first delete Debit '
                    'Account Move!'))
            check.signal_workflow('debited_handed')
        return True


    def action_cancel_deposit(self):
        for check in self:
            if check.deposit_account_move_id:
                raise ValidationError(_(
                    'To cancel a deposit you must first delete the Deposit '
                    'Account Move!'))
            check.signal_workflow('cancel_deposit')
        return True


    def action_cancel_return(self):
        for check in self:
            if check.return_account_move_id:
                raise ValidationError(_(
                    'To cancel a deposit you must first delete the Return '
                    'Account Move!'))
            check.signal_workflow('cancel_return')
        return True

    # TODO implementar para caso issue y third
    #
    # def action_cancel_change(self):
    #     for check in self:
    #         if check.replacing_check_id:
    #             raise ValidationError(_(
    #                 'To cancel a return you must first delete the replacing '
    #                 'check!'))
    #         check.signal_workflow('cancel_change')
    #     return True



    def check_check_cancellation(self):
        for check in self:
            if check.type == 'issue_check' and check.state not in [
                    'handed', 'handed']:
                raise ValidationError(_(
                    'You can not cancel issue checks in states other than '
                    '"handed or "handed". First try to change check state.'))
            # third checks received
            elif check.type == 'third_check' and check.state not in [
                    'handed', 'holding']:
                raise ValidationError(_(
                    'You can not cancel third checks in states other than '
                    '"handed or "holding". First try to change check state.'))
            elif check.type == 'third_check' and check.third_handed_voucher_id:
                raise ValidationError(_(
                    'You can not cancel third checks that are being used on '
                    'payments'))
        return True


    def action_cancel(self):
        for check in self:

            if check.deposit_account_move_id:
                raise ValidationError(_(
                    'Para cancelar un cheque depositado primero deben eliminarse todos los asientos asociados '
                    ))
            else:
                check.write({'state': 'cancel'})

