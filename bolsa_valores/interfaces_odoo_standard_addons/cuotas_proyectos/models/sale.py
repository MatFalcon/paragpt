from locale import currency
from odoo import models, api, fields, exceptions
from datetime import datetime,date,timedelta


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    cuotas_ids = fields.One2many(
        'sale.order.cuota', 'order_id', string="Cuotas")
    hitos_ids = fields.One2many('sale.order.hito', 'order_id', string="Hitos")

    def crear_cuotas(self):
        if any(self.cuotas_ids.filtered(lambda x:x.tipo_facturacion=='hito')) and (any(self.hitos_ids.filtered(lambda h:not h.milestone_id)) or not self.hitos_ids):
            raise exceptions.ValidationError('Existen cuotas con tipo de facturación por hitos pero no existen hitos o aún no fueron creados en el proyecto')
        if not self.project_ids:
            raise exceptions.ValidationError('No existe un proyecto asociado al presupuesto')
        for cuota in self.cuotas_ids.filtered(lambda x: not x.cuota_id):
            cuota_id = self.env['cuotas.cuota'].create(
                {'nro_cuota': cuota.name,
                 'partner_id': self.partner_id.id if cuota.tipo_cuota=='sale' else cuota.proveedor_id.id,
                 'tipo_facturacion': cuota.tipo_facturacion,
                 'project_id': self.project_ids[0].id,
                 'milestone_id': cuota.milestone_id.id if cuota.milestone_id else False,
                 'fecha_facturacion': cuota.fecha_facturacion,
                 'fecha_vencimiento': cuota.fecha_facturacion + timedelta(days=10),
                 'order_id': self.id,
                 'currency_id':cuota.currency_id.id,
                 'monto_cuota': cuota.amount,
                 'tipo_cuota': cuota.tipo_cuota,
                 'product_id':cuota.product_id.id,
                 'analytic_account_id':self.analytic_account_id.id if self.analytic_account_id else False

                 })
            cuota.write({'cuota_id':cuota_id.id})
            if cuota_id:
                cuota_id.button_confirmar()

        return

    def crear_hitos(self):
        if self.project_ids:
            project_id = self.project_ids[0]
            # if not project_id.milestone_ids:
            for hito in self.hitos_ids.filtered(lambda x: not x.milestone_id).sorted(key=lambda x: x.sequence):
                milestone_id = self.env['project.milestone'].create({
                    'project_id': project_id.id,
                    'name': hito.name,
                    'deadline': hito.deadline
                })
                hito.write({'milestone_id': milestone_id.id})
            # else:
            #    raise exceptions.ValidationError(
            #        'Ya existen hitos en el proyecto %s' % project_id.name)
        else:
            raise exceptions.ValidationError(
                'No existen proyectos para este presupuesto')
        return


class SaleOrderCuota(models.Model):
    _name = 'sale.order.cuota'
    _description = 'Cuota de presupuesto'

    sequence = fields.Integer(string="Secuencia")
    order_id = fields.Many2one('sale.order')
    name = fields.Char(string='Descripción')
    currency_id = fields.Many2one('res.currency', string="Moneda")
    tipo_cuota = fields.Selection(string="Tipo de cuota", selection=[(
        'sale', 'Ingreso'), ('purchase', 'Egreso')], required=True, default='sale')
    proveedor_id=fields.Many2one("res.partner",string="Proveedor")
    amount = fields.Monetary(string="Monto")
    fecha_vencimiento = fields.Date(string="Fecha de vencimiento")
    fecha_facturacion= fields.Date(string="Fecha de facturación")
    tipo_facturacion = fields.Selection(string="Tipo de facturación", selection=[(
        'fecha', 'Por fecha de vencimiento'), ('hito', 'Por hito')], default='fecha')
    milestone_id = fields.Many2one('project.milestone', string="Hito")
    cuota_id = fields.Many2one('cuotas.cuota', string="Cuota del presupuesto")
    project_ids = fields.Many2many(
        'project.project', related='order_id.project_ids')

    product_id=fields.Many2one('product.product',string="Producto")


    @api.onchange('milestone_id')
    def establecer_fecha(self):
        self.fecha_vencimiento = self.milestone_id.deadline


class SaleOrderHito(models.Model):
    _name = 'sale.order.hito'
    _description = 'Hito del presupuesto'

    sequence = fields.Integer(string="Secuencia")
    order_id = fields.Many2one('sale.order')
    name = fields.Char(string='Descripción')
    deadline = fields.Date(string="Fecha de cierre")
    milestone_id = fields.Many2one(
        'project.milestone', string="Hito del proyecto")
