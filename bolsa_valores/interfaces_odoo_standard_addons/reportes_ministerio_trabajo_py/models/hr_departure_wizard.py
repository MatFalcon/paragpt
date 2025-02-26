from odoo import api, models, fields, exceptions


class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'

    def action_register_departure(self):
        # reportes_ministerio_trabajo/models/hr_departure_wizard.py
        r = super(HrDepartureWizard, self).action_register_departure()
        self.employee_id.contract_ids.write({'state': 'cancel'})
        return r
