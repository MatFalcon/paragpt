from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund'):
                for line in move.invoice_line_ids:
                    if line.analytic_distribution:
                        analytic_distribution = line.analytic_distribution.copy()
                        first_key = list(analytic_distribution.keys())[0] if analytic_distribution else None
                        if first_key:
                            analytic_distribution[first_key] = 100.0
                            line.write({'analytic_distribution': analytic_distribution})
        return res
