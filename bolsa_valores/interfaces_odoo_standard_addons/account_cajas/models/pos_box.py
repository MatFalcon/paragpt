from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CashBox(models.TransientModel):
    _register = False

    name = fields.Char(string='Motivo', required=True)
    amount = fields.Float(string='Importe', digits=0, required=True)

    
    def run(self):
        context = dict(self._context or {})
        active_model = context.get('active_model', False)
        active_ids = context.get('active_ids', [])

        records = self.env[active_model].browse(active_ids)

        return self._run(records)

    
    def _run(self, records):
        for box in self:
            for record in records:
                if not record.st_efectivo.journal_id:
                    raise UserError(_("Please check that the field 'Journal' is set on the Bank Statement"))
                if not record.st_efectivo.journal_id.company_id.transfer_account_id:
                    raise UserError(_("Please check that the field 'Transfer Account' is set on the company."))
                box._create_bank_statement_line(record)
        return {}

    
    def _create_bank_statement_line(self, record):
        if record.state == 'confirm':
            raise UserError(_("No puede ingresar/sacar dinero en una sesión de caja finalizada"))
        values = self._calculate_values_for_statement_line(record)
        return record.st_efectivo.write({'line_ids': [(0, False, values)]})


class CashBoxIn(CashBox):
    _name = 'cash.box.in'
    _description = 'Cash Box In'

    ref = fields.Char('Reference')

    
    def _calculate_values_for_statement_line(self, record):
        if not record.st_efectivo.journal_id.company_id.transfer_account_id:
            raise UserError(_("You have to define an 'Internal Transfer Account' in your cash register's journal."))
        return {
            'date': fields.Datetime.now(),
            # 'statement_id': record.id,
            # 'journal_id': record.st_efectivo.journal_id.id,
            'amount': abs(self.amount) or 0.0,
            # 'account_id': record.st_efectivo.journal_id.company_id.transfer_account_id.id,
            # 'ref': '%s' % (self.ref or ''),
            'name': self.name,
        }


class CashBoxOut(CashBox):
    _name = 'cash.box.out'
    _description = 'Cash Box Out'

    
    def _calculate_values_for_statement_line(self, record):
        if not record.st_efectivo.journal_id.company_id.transfer_account_id:
            raise UserError(_("You have to define an 'Internal Transfer Account' in your cash register's journal."))
        amount = self.amount or 0.0
        return {
            'date': fields.Datetime.now(),
            # 'statement_id': record.id,
            # 'journal_id': record.st_efectivo.journal_id.id,
            # 'account_id': record.st_efectivo.journal_id.company_id.transfer_account_id.id,
            'amount': - abs(amount),
            'name': self.name,
        }