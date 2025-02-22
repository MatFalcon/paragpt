from odoo import models, fields, api, exceptions


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    crossovered_budget_line_id = fields.Many2one('crossovered.budget.lines', string="Linea de Presupuesto")

    @api.onchange('account_analytic_id','product_id', 'order_id.date_order')
    @api.depends('account_analytic_id','product_id', 'order_id.date_order')
    def onchangeAccountAnalytic(self):
        for i in self:
            if i.product_id and i.order_id.date_order:
                search_domain = [('crossovered_budget_id.state','=','validate'),
                                 ('crossovered_budget_id.date_from','<=',i.order_id.date_order.date()),
                                 ('crossovered_budget_id.date_to','>=',i.order_id.date_order.date())]
                if i.product_id.property_account_expense_id:
                    search_domain.append(('general_budget_id.account_ids','=',i.product_id.property_account_expense_id.id))
                if i.account_analytic_id:
                    search_domain.append(('analytic_account_id','=',i.account_analytic_id.id))
                if i.product_id.property_account_expense_id or i.account_analytic_id:
                    situacion_presupuestaria = self.env['crossovered.budget.lines'].search(search_domain)
                    if situacion_presupuestaria:
                        self.write({'crossovered_budget_line_id':situacion_presupuestaria[0].id})
                    else:
                        self.write({'crossovered_budget_line_id':False})
