# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
##############################################################################
# For copyright and license notices, see __odoo__.py file in module root
# directory
##############################################################################


class account_journal(models.Model):
    _inherit = 'account.journal'

    checkbook_ids = fields.One2many(
        'account.checkbook',
        'journal_id',string="Chequeras"
        )



    def _get_payment_subtype(self):
        selection = super(account_journal, self)._get_payment_subtype()
        selection.append(('issue_check', _('Cheques Propios')))
        selection.append(('third_check', _('Cheques de Terceros')))
        # same functionality as checks, no need to have both for now
        # selection.append(('promissory', _('Promissory Note')))
        return selection

class voucher(models.Model):
    _inherit = 'account.voucher'

    check_id = fields.Many2one('account.check', string="Cheque", tracking=True)
    diario_tipo_cheque = fields.Char(string='Payment Subtype', compute='_compute_diario_tipo_cheque', store=True)

    @api.depends('payment_journal_id')
    def _compute_diario_tipo_cheque(self):
        """Este método actualiza diario_tipo_cheque basado en payment_journal_id.payment_subtype
            para poder ocultar en la vista cuando el diario no es issue_check."""
        for record in self:
            record.diario_tipo_cheque = record.payment_journal_id.payment_subtype if record.payment_journal_id else False

