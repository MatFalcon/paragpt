# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __odoo__.py file in module root
# directory
##############################################################################
from odoo import fields, models, api, _,exceptions
import logging

_logger = logging.getLogger(__name__)


class account_checkbook(models.Model):

    _name = 'account.checkbook'
    _description = 'Account Checkbook'
    _inherit = ['mail.thread']

    def _get_next_check_number(self):
        cr=self.env.cr.execute('select max(number) from account_check where checkbook_id =%s', (self.id,))
        number = self.env.cr.fetchone()[0]
        if number:
            self.next_check_number = number + 1
        else:
            self.next_check_number = self.range_from

    name = fields.Char(
        'Nombre', size=30,required=True,tracking=True)
    issue_check_subtype = fields.Selection(
        [('deferred', 'Deferred'), ('currents', 'Currents')],
        string='Subtipo',
        required=True,
        default='deferred',
        help='The only difference bewteen Deferred and Currents is that when '
        'delivering a Deferred check a Payment Date is Require',
        states={'draft': [('readonly', False)]})
    debit_journal_id = fields.Many2one(
        'account.journal', 'Diario de Debito',
        help='It will be used to make the debit of the check on checks ',
        required=False,tracking=True,
        domain=[('type', '=', 'bank')],
        context={'default_type': 'bank'})
    journal_id = fields.Many2one(
        'account.journal', 'Diario',
        help='Journal where it is going to be used',
        tracking=True, required=True, domain=[('type', '=', 'bank')],
        context={'default_type': 'bank'})
    range_from = fields.Integer(
        'Numero desde:', tracking=True, required=True)
    range_to = fields.Integer(
        'Numero Hasta', tracking=True, required=True)
    next_check_number = fields.Char(
        compute='_get_next_check_number',
        string=_('Proximo Numero'),)
    padding = fields.Integer(
        'Cantidad de Digitos',
        default=8,
        required=True,tracking=True,
        help="automatically adds some '0' on the left of the 'Number' to get "
        "the required padding size.")
    company_id = fields.Many2one(
        'res.company',
        related='journal_id.company_id',
        requirde=True, readonly=True,
        string='Company', store=True)
    issue_check_ids = fields.One2many(
        'account.check', 'checkbook_id', string='Issue Checks', readonly=True,)
    state = fields.Selection(
        [('draft', 'Draft'), ('active', 'In Use'), ('used', 'Used')],
        string='State', readonly=True, default='draft', copy=False)

    _order = "name"

    @api.onchange('debit_journal_id')
    def set_journal_id(self):
        for rec in self:
            if rec.debit_journal_id:
                rec.journal_id = rec.debit_journal_id
            else:
                rec.journal_id = False
    @api.constrains('padding')
    @api.onchange('padding')
    def check_padding(self):
        if self.padding > 32:
            raise ValidationError(
                _('Padding must be lower than 32'))

    #
    @api.constrains('debit_journal_id', 'journal_id')
    def check_journals(self):
        if self.journal_id.company_id != self.debit_journal_id.company_id:
            raise ValidationError(
                _('Journal And Debit Journal must belong to the same company'))

    #
    def unlink(self):
        if self.state not in ('draft'):
            raise ValidationError(
                _('You can drop the checkbook(s) only in draft state !'))
        return super(account_checkbook, self).unlink()


    def set_used(self):
        self.write({'state': 'used'})
        return True


    def set_active(self):
        self.write({'state': 'active'})
        return True


    def set_draft(self):
        self.write({'state': 'draft'})
        return True
