from odoo import fields, models, exceptions, api , _
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError

class AuxiliaryLaborCalculation(models.Model):
    _name = "presale.auxiliary_labor_calculation"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    cal_order_id = fields.Many2one('presale.auxiliary_calculation_per_floor',string="Labor per floor", copy=True)
    order_id = fields.Many2one(related='cal_order_id.floor_order_id',store=True, copy=True)
    workdays = fields.Float(string="Workdays", related='cal_order_id.workdays', store=True, copy=True)
    qty_labor = fields.Float(string="Qty. Employee", tracking=True, copy=True)
    labor_unit_cost = fields.Float(string="Unit Cost", tracking=True, copy=True)
    labor_type = fields.Many2one('presale.labor_type', string="Labor type", copy=True, tracking=True)
    subtotal_amount = fields.Float(string="Subtotal Amount", compute="calculate_labor_per_floor", store=True, copy=True)

    @api.onchange('labor_type')
    def get_labor_rate(self):
        for rec in self:
            # get_working_rate = self.env['presale.working_rate'].search([('labor_type_id','=',rec.labor_type.id)]) # ,('team_id','=',rec.team_id.id)
            if rec.labor_type:
                print(f"[TEST-ID-SELECTION:] {rec.order_id.id}")
                get_working_rate = self.env['presale.labor_used'].search([('labor_type','=',rec.labor_type.id),('presale_labor_ids','=', rec.order_id.id)]) # ,('team_id','=',rec.team_id.id)
                if get_working_rate:
                    # rec.labor_unit_cost = get_working_rate.rate
                    rec.labor_unit_cost = get_working_rate.labor_unit_cost



    @api.depends('workdays','labor_unit_cost','qty_labor')
    def calculate_labor_per_floor(self):
        for rec in self:
            if rec.workdays and rec.qty_labor and not rec.labor_type:
                 raise ValidationError("Debe seleccionar un tipo de Mano de Obra para realizar el mimso calculo!")
            else:
                rec.subtotal_amount = rec.workdays * rec.qty_labor * rec.labor_unit_cost

    # def unlink(self):
    #     for record in self:
    #         if record.cal_order_id:
    #             labor_type_ids = record.cal_order_id.labor_type_ids.filtered(lambda x: x.labor_type == record.labor_type)
    #             labor_type_ids.unlink()

    #     return super(AuxiliaryLaborCalculation, self).unlink()

    
    # def _update_summary_laborer(self):
    #     labor_type_summary = {}
    #     for rec in self:
    #         # labor_type = rec.labor_type
    #         # labor_type_summary[labor_type.id] = labor_type_summary.get(labor_type.id, 0.0) + rec.subtotal_amount
    #         for cal in rec.cal_order_id:
    #             labor_type = rec.labor_type
    #             subtotal_amount = rec.subtotal_amount
    #             labor_type_id = labor_type.id
    #             labor_type_summary[labor_type_id] = labor_type_summary.get(labor_type_id, 0.0) + subtotal_amount

    #     for labor_type_id, subtotal_amount in labor_type_summary.items():
    #         print(f"[LABOR:] {labor_type_id}, [AMOUNT:] {subtotal_amount}")
    #         summary_laborer = self.env['presale.auxiliary_summary_laborer'].search([('labor_type', '=', labor_type_id)])
    #         if summary_laborer:
    #             print("UPDATE SUMMARY ITEMS")
    #             summary_laborer.write({'cost_laborers_per_day': subtotal_amount})
    #         else:
    #             print("CREATE SUMMARY ITEMS")
    #             self.env['presale.auxiliary_summary_laborer'].create({'presale_labor_summary_ids': rec.order_id.id,'labor_type': labor_type_id, 'day_laborers': 1 ,'cost_laborers_per_day': subtotal_amount})


    # @api.model
    # def create(self, values):
    #     record = super(AuxiliaryLaborCalculation, self).create(values)
    #     record._update_summary_laborer()
    #     return record


    # def write(self, values):
    #     result = super(AuxiliaryLaborCalculation, self).write(values)
    #     self._update_summary_laborer()
    #     return result


    # def create_update_auxiliary_table(self):
    #     for rec in self:
    #         if rec.cal_order_id:
    #             auxiliary_labor_table = self.env['presale.auxiliary_labor_table'].search([
    #                 ('order_id_aux', '=', rec.cal_order_id.floor_order_id.id),
    #                 ('labor_type', '=', rec.labor_type.id)], limit=1)
                
    #             if auxiliary_labor_table:
    #                 auxiliary_labor_table.qty_labor = rec.qty_labor
    #                 auxiliary_labor_table.labor_unit_cost = rec.labor_unit_cost
    #             else:
    #                 test = self.env['presale.auxiliary_labor_table'].create({
    #                     'order_id_aux': rec.cal_order_id.floor_order_id.id,
    #                     'labor_type': rec.labor_type.id,
    #                     # 'qty_labor': rec.workdays,
    #                     # 'labor_unit_cost': rec.labor_unit_cost
    #                     })
    #                 test.get_labor_rate()

    # @api.model
    # def create(self, values):
    #     record = super(AuxiliaryLaborCalculation, self).create(values)
    #     record.create_update_auxiliary_table()
    #     return record
    

    # def write(self, values):
    #     result = super(AuxiliaryLaborCalculation, self).write(values)
    #     self.create_update_auxiliary_table()
    #     return result


class AuxiliarySummaryLaborCalculation(models.Model):
    _name = "presale.auxiliary_summary_laborer"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    presale_labor_summary_ids = fields.Many2one('presale.order', 'Presale Order', copy=True)
    labor_type = fields.Many2one('presale.labor_type', string="Labor type", copy=True, tracking=True)
    day_laborers = fields.Float(string="Day Laborers")
    cost_laborers_per_day = fields.Float(string="Cost of day laborers per day")






    