from odoo import models,fields,api,exceptions,_


class AccountMove(models.Model):
    _inherit = 'account.move'


    @api.onchange('currency_id','invoice_line_ids')
    def onchange_currency_id_(self):
        self._onchange_partner_id()





    """cuando modifico el currency_id, no se llama a esta funcion de abajo. pero si cuando cambio el partner, por eso cree el onchange de arriba para 
    que si se ejecute esta funcion al modificar la moneda."""

    @api.onchange('partner_id','currency_id')
    def _onchange_partner_id(self):
        self = self.with_company(self.journal_id.company_id)

        warning = {}
        if self.partner_id:
            rec_account = self.partner_id.property_account_receivable_id
            pay_account = self.partner_id.property_account_payable_id
            cambio_cuenta=False
            if self.currency_id!=self.env.company.currency_id:
                #if self.partner_id.property_ext_account_receivable_id and self.partner_id.property_ext_account_receivable_id.currency_id==self.currency_id:
                if self.currency_id.receivable_account_id:
                    rec_account = self.currency_id.receivable_account_id
                else:
                    raise exceptions.ValidationError('No está configurada la cuenta a cobrar en moneda extranjera para %s'%self.currency_id.name)
                #cambio_cuenta=True
                #if self.partner_id.property_ext_account_payable_id and self.partner_id.property_ext_account_payable_id.currency_id==self.currency_id: 
                if self.currency_id.payable_account_id:
                    pay_account = self.currency_id.payable_account_id
                else:
                    raise exceptions.ValidationError('No está configurada la cuenta a pagar en moneda extranjera para %s'%self.currency_id.name)
                cambio_cuenta=True

            if not rec_account and not pay_account:
                action = self.env.ref('account.action_account_config')
                msg = _('Cannot find a chart of accounts for this company, You should configure it. \nPlease go to Account Configuration.')
                raise exceptions.RedirectWarning(msg, action.id, _('Go to the configuration panel'))
            p = self.partner_id
            if p.invoice_warn == 'no-message' and p.parent_id:
                p = p.parent_id
            if p.invoice_warn and p.invoice_warn != 'no-message':
                # Block if partner only has warning but parent company is blocked
                if p.invoice_warn != 'block' and p.parent_id and p.parent_id.invoice_warn == 'block':
                    p = p.parent_id
                warning = {
                    'title': _("Warning for %s", p.name),
                    'message': p.invoice_warn_msg
                }
                if p.invoice_warn == 'block':
                    self.partner_id = False
                    return {'warning': warning}

        if self.is_sale_document(include_receipts=True) and self.partner_id:
            self.invoice_payment_term_id = self.partner_id.property_payment_term_id or self.invoice_payment_term_id
            new_term_account = self.partner_id.commercial_partner_id.property_account_receivable_id
            if cambio_cuenta:
                new_term_account=rec_account
        elif self.is_purchase_document(include_receipts=True) and self.partner_id:
            self.invoice_payment_term_id = self.partner_id.property_supplier_payment_term_id or self.invoice_payment_term_id
            new_term_account = self.partner_id.commercial_partner_id.property_account_payable_id
            if cambio_cuenta:
                new_term_account=pay_account
        else:
            new_term_account = None
        
        

        for line in self.line_ids:
            line.partner_id = self.partner_id.commercial_partner_id

            if new_term_account and line.account_id.user_type_id.type in ('receivable', 'payable'):
                line.account_id = new_term_account

        self._compute_bank_partner_id()
        bank_ids = self.bank_partner_id.bank_ids.filtered(lambda bank: bank.company_id is False or bank.company_id == self.company_id)
        self.partner_bank_id = bank_ids and bank_ids[0]

        # Find the new fiscal position.
        delivery_partner_id = self._get_invoice_delivery_partner_id()
        self.fiscal_position_id = self.env['account.fiscal.position'].get_fiscal_position(
            self.partner_id.id, delivery_id=delivery_partner_id)
        self._recompute_dynamic_lines()
        if warning:
            return {'warning': warning}
