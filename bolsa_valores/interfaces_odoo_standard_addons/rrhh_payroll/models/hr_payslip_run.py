from odoo import api, fields, models
import datetime
from calendar import monthrange


class HrPaylslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(compute='_get_state')

    def _get_state(self):
        for this in self:
            slip_ids_states = this.slip_ids.mapped('state')
            state = 'draft'
            if 'draft' in slip_ids_states:
                state = 'verify'
            elif 'verify' in slip_ids_states:
                state = 'verify'
            elif 'done' in slip_ids_states:
                state = 'close'
            elif 'paid' in slip_ids_states:
                state = 'paid'
            this.state = state

    def action_validate(self):
        for this in self:
            for slip in this.slip_ids:
                # slip.reset_worked_days()
                slip.compute_sheet()
                slip.action_payslip_done()

    def reset_worked_days(self):
        for this in self:
            payslips = this.slip_ids.filtered(lambda x: x.state in ['draft', 'verify'])
            payslips.reset_worked_days()
            payslips.compute_sheet()
