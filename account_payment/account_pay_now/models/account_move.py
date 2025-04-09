# © 2016 ADHOC SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError, UserError

class ValidateAccountMove(models.TransientModel):
    _inherit = "validate.account.move"

    def validate_move(self):
        if self._context.get('active_model') == 'account.move':
            domain = [('id', 'in', self._context.get('active_ids', [])), ('state', '=', 'draft')]
        elif self._context.get('active_model') == 'account.journal':
            domain = [('journal_id', '=', self._context.get('active_id')), ('state', '=', 'draft')]
        else:
            raise UserError(_("Missing 'active_model' in context."))
        moves = self.env['account.move'].search(domain).filtered('line_ids')
        res = super().validate_move()
        moves.pay_now()
        return res

class AccountMove(models.Model):
    _inherit = "account.move"


    pay_now_journal_id = fields.Many2one(
        'account.journal',
        'Diario de pago directo',
        help='If you set a journal here, after invoice validation, the invoice'
        ' will be automatically paid with this journal. As manual payment'
        'method is used, only journals with manual method are shown.',
        readonly=True,
        states={'draft': [('readonly', False)]},
        # use copy false for two reasons:
        # 1. when making refund it's safer to make pay now empty (specially if automatic refund validation is enable)
        # 2. on duplicating an invoice it's safer also
        copy=False,
    )

    def pay_now(self):
        # validate_payment = not self._context.get('validate_payment')
        for rec in self:
            to_reconcile = self.env['account.move.line']

            pay_journal = rec.pay_now_journal_id
            if pay_journal and rec.state == 'posted' and rec.payment_state in ['not_paid', 'patial']:
                # si bien no hace falta mandar el partner_type al paygroup
                # porque el defaults lo calcula solo en funcion al tipo de
                # cuenta, es mas claro mandarlo y podria evitar error si
                # estamos usando cuentas cruzadas (payable, receivable) con
                # tipo de factura
                if rec.move_type in ['in_invoice', 'in_refund']:
                    partner_type = 'supplier'
                    payment_type = 'outbound'
                    payment_methods = pay_journal.outbound_payment_method_line_ids.payment_method_id
                    domain_pago = ([('account_internal_type', '=', 'payable')])

                else:
                    partner_type = 'customer'
                    payment_type = 'inbound'
                    payment_methods = pay_journal.inbound_payment_method_line_ids.payment_method_id
                    domain_pago = ([('account_internal_type', '=', 'receivable')])

                pay_context = {
                    'to_pay_move_line_ids': (rec.open_move_line_ids.ids),
                    'default_company_id': rec.company_id.id,
                    'default_partner_type': partner_type,
                }
                payment_method = payment_methods.filtered(
                    lambda x: x.code == 'manual')
                if not payment_method:
                    raise ValidationError(_(
                        'Pay now journal must have manual method!'))

                payment = rec.env['account.payment'].create({
                            'date': rec.invoice_date,
                            'partner_id': rec.commercial_partner_id.id,
                            'payment_type' : payment_type,
                            'amount': rec.amount_total,
                            'journal_id': pay_journal.id,
                            'payment_method_id': payment_method.id,
                            'company_id': rec.company_id.id,

                })
                payment.action_post()
                to_reconcile += (rec.line_ids.filtered_domain(domain_pago))

                payment_lines = payment.line_ids.filtered_domain(domain_pago)
                for account in payment_lines.account_id:
                    (payment_lines + to_reconcile) \
                        .filtered_domain([('account_id', '=', account.id), ('reconciled', '=', False)]).reconcile()

    def action_view_payment_groups(self):
        if self.move_type in ('in_invoice', 'in_refund'):
            action = self.env.ref('account_payment_group.action_account_payments_group_payable')
        else:
            action = self.env.ref('account_payment_group.action_account_payments_group')

        result = action.sudo().read()[0]

        if len(self.payment_group_ids) != 1:
            result['domain'] = [('id', 'in', self.payment_group_ids.ids)]
        elif len(self.payment_group_ids) == 1:
            res = self.env.ref(
                'account_payment_group.view_account_payment_group_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.payment_group_ids.id
        return result

    @api.onchange('journal_id')
    def _onchange_journal_reset_pay_now(self):
        # while not always it should be reseted (only if changing company) it's not so usual to set pay now first
        # and then change journal
        self.pay_now_journal_id = False

    def button_draft(self):
        self.filtered(lambda x: x.state == 'posted' and x.pay_now_journal_id).write({'pay_now_journal_id': False})
        return super().button_draft()

    def _get_last_sequence_domain(self, relaxed=False):
        """ para transferencias no queremos que se enumere con el ultimo numero de asiento porque podria ser un
        pago generado por un grupo de pagos y en ese caso el numero viene dado por el talonario de recibo/pago.
        Para esto creamos campo related stored a payment_group_id de manera de que un asiento sepa si fue creado
        o no desde unpaymetn group
        TODO: tal vez lo mejor sea cambiar para no guardar mas numero de recibo en el asiento, pero eso es un cambio
        gigante
        """
        if self.journal_id.type in ('cash', 'bank') :
            # mandamos en contexto que estamos en esta condicion para poder meternos en el search que ejecuta super
            # y que el pago de referencia que se usa para adivinar el tipo de secuencia sea un pago sin tipo de
            # documento
            where_string, param = super(
                AccountMove, self.with_context(without_payment_group=True))._get_last_sequence_domain(relaxed)
            where_string += " AND payment_group_id is Null"
        else:
            where_string, param = super(AccountMove, self)._get_last_sequence_domain(relaxed)
        return where_string, param

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if self._context.get('without_payment_group'):
            args += [('payment_group_id', '=', False)]
        return super()._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)
