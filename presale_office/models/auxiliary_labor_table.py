from odoo import fields, models, exceptions, api , _
from odoo.exceptions import ValidationError

class AuxiliaryLaborTable(models.Model):
    _name = "presale.auxiliary_labor_table"
    _description = "Presale Auxiliary Labor Table"

    order_id_aux = fields.Many2one('presale.order', 'Presale Order', copy=True)
    labor_type = fields.Many2one('presale.labor_type', string="Labor type", copy=True, tracking=True)
    qty_labor = fields.Float(string="Quantity", tracking=True, copy=True)
    labor_unit_cost = fields.Float(string="Unit Cost", tracking=True, copy=True)
    labor_total_cost = fields.Float(string="Total Cost", compute="calculate_man_day_cost", store=True, copy=True)
    overtime_one = fields.Float(string="Ex. Hs. 01", compute="calculate_man_day_cost", store=True, copy=True)
    subtotal_one = fields.Float(string="Subtotal", compute="calculate_man_day_cost", store=True, copy=True)
    overtime_two = fields.Float(string="Ex. Hs. 02", compute="calculate_man_day_cost", store=True, copy=True)
    subtotal_two = fields.Float(string="Subtotal", compute="calculate_man_day_cost", store=True, copy=True)

    # @api.onchange('labor_type')
    # def get_labor_rate(self):
    #     for rec in self:
    #         get_working_rate = self.env['presale.working_rate'].search([('labor_type_id','=',rec.labor_type.id)]) # ,('team_id','=',rec.team_id.id)
    #         if get_working_rate:
    #             rec.labor_unit_cost = get_working_rate.rate


    @api.depends('qty_labor', 'labor_unit_cost', 'labor_total_cost', 'overtime_one', 'overtime_two')
    def calculate_man_day_cost(self):
        for rec in self:
            rec.labor_total_cost =  rec.labor_unit_cost * rec.qty_labor
            rec.overtime_one = ((rec.labor_unit_cost / 8) * 1.5)
            rec.subtotal_one = rec.qty_labor * rec.overtime_one
            rec.overtime_two = ((rec.labor_unit_cost / 8) * 2)
            rec.subtotal_two = rec.qty_labor * rec.overtime_two
            # print(f"[SUMA]{sum(rec.subtotal_one)}")


