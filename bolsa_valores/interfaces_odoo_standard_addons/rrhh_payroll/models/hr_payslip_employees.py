from odoo import api, fields, models
import datetime
from calendar import monthrange


class HrPaylslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def compute_sheet(self):
        self.env['hr.work.entry'].search([]).sudo().unlink()
        r = super(HrPaylslipEmployees, self).compute_sheet()
        for this in self.env[r.get('res_model')].browse(r.get('res_id')):
            if not self.structure_id:
                for slip in this.slip_ids:
                    slip.struct_id = slip.contract_id.structure_id
                this.slip_ids.reset_worked_days()
                this.slip_ids.compute_sheet()
        return r

    def _check_undefined_slots(self, work_entries, payslip_run):
        return
