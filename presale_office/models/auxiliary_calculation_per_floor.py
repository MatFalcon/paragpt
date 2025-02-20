from odoo import fields, models, exceptions, api , _
from datetime import datetime, timedelta
from lxml import etree
from odoo.exceptions import ValidationError



class LaborToBeUsed(models.Model):
    _name = "presale.labor_used"

    presale_labor_ids = fields.Many2one('presale.order', 'Presale Order', store=True, copy=True)
    labor_type = fields.Many2one('presale.labor_type', string="Labor type", copy=True, tracking=True)
    labor_unit_cost = fields.Float(string="Unit Cost", tracking=True)
    fixed_month = fields.Float(string="Fixed per Month", compute="calculate_man_day_cost", store=True, copy=True)



    @api.onchange('labor_type')
    def get_labor_rate(self):
        for rec in self:
            get_working_rate = self.env['presale.working_rate'].search([('labor_type_id','=',rec.labor_type.id)])
            if get_working_rate:
                rec.labor_unit_cost = get_working_rate.rate


    @api.depends('labor_unit_cost')
    def calculate_man_day_cost(self):
        for rec in self:
            rec.fixed_month =  rec.labor_unit_cost * 24

    
    @api.constrains('labor_type','presale_labor_ids')
    def _check_labor_used(self):
        for rec in self:
            currency_rates = self.env['presale.labor_used'].search_count([('labor_type','=',rec.labor_type.id),('presale_labor_ids','=',rec.presale_labor_ids.id)])
            if currency_rates > 1:
                raise ValidationError(_('There is already a labor used rate for the labor used table... To add a new cup, select a different one!'))

    
    # @api.model
    # def create(self, vals):
    #     print("Create function is called")
    #     print("Vals:", vals)
        
    #     vals['labor_type'] = 1
    #     vals['labor_unit_cost'] = 1000

    #     result = super(LaborToBeUsed, self).create(vals)
    #     return result



    # def create_calculation_per_floor(self):
    #     for rec in self:
    #         if rec.presale_labor_ids:
    #             for labor_order in rec.presale_labor_ids:
    #                 if labor_order.labor_per_floor_ids:
    #                     for labor_per_floor in labor_order.labor_per_floor_ids:
    #                         # Verificamos si el labor_type ya existe en labor_type_ids
    #                         existing_labor_type = labor_per_floor.labor_type_ids.filtered(lambda x: x.labor_type == rec.labor_type)
    #                         if existing_labor_type:
    #                             # Actualizamos el registro existente
    #                             existing_labor_type.write({
    #                                 'labor_unit_cost': rec.labor_unit_cost,
    #                             })
    #                         else:
    #                             # Creamos un nuevo registro en labor_type_ids
    #                             self.env['presale.auxiliary_labor_calculation'].create({
    #                                 'cal_order_id': labor_per_floor.id,
    #                                 'labor_type': rec.labor_type.id,
    #                                 'labor_unit_cost': rec.labor_unit_cost,
    #                                 # Otras columnas que puedas necesitar
    #                             })

    # def create(self, values):
    #     record = super(LaborToBeUsed, self).create(values)
    #     record.create_calculation_per_floor()
    #     return record

    # def write(self, values):
    #     result = super(LaborToBeUsed, self).write(values)
    #     self.create_calculation_per_floor()
    #     return result


class AuxiliaryCalculationPerFloor(models.Model):
    _name = "presale.auxiliary_calculation_per_floor"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", tracking=True, copy=True)
    floor_order_id = fields.Many2one('presale.order', 'Presale Order', store=True, copy=True)
    num_items = fields.Integer(string="No. Items", copy=True)
    workdays = fields.Float(string="Workdays", tracking=True, copy=True)
    labor_type_ids = fields.One2many('presale.auxiliary_labor_calculation', 'cal_order_id', string="Logistic", tracking=True, copy=True)


    # def default_get(self, fields_list):
    #     res = super(AuxiliaryCalculationPerFloor, self).default_get(fields_list)

    #     # Obtener el valor de 'floor_order_id' del diccionario 'res'
    #     floor_order_id = res.get('floor_order_id')
    #     print("test")
    #     print(floor_order_id)

    #     labor_type_values = []
    #     if floor_order_id:
    #         print(floor_order_id)
    #         labor_used_records = self.env['presale.labor_used'].search([('presale_labor_ids', '=', floor_order_id)])
    #         for labor_used in labor_used_records:
    #             print(f"[TEST:] {labor_used.labor_type.name}")
    #             labor_type_values.append((0, 0, {
    #                 'labor_type': labor_used.labor_type.id,
    #                 'labor_unit_cost': labor_used.labor_unit_cost,
    #             }))

    #     res.update({'labor_type_ids': labor_type_values})
    #     return res
    