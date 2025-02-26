from email.policy import default
from odoo import api, fields, models,exceptions
import datetime
from dateutil.relativedelta import *

class WizardGenerarCuota(models.TransientModel):
    _name = 'cuotas.wizard.generar.cuota'
    _description = 'Generar cuota'
    

    partner_id=fields.Many2one('res.partner',string="Empresa",required=True)
    product_id=fields.Many2one('product.product',string="Producto",required=True)
    currency_id=fields.Many2one('res.currency',string="Moneda",required=True,default=lambda self:self.env.company.currency_id)
    monto_cuota=fields.Monetary(string="Monto",required=True)
    cant_cuotas=fields.Integer(string="Cantidad de cuotas mensuales",default=1,required=True)
    descuento_porcentaje=fields.Float(string="Descuento %",default=0)
    fecha_vencimiento=fields.Date(string="Fecha venc. 1era cuota",required=True)
    descuentos_id = fields.Many2one('curso_cuotas.descuentos', string="Elegir descuento")
    tipo_cuota = fields.Selection(string="Tipo de cuota", selection=[(
        'sale', 'Ingreso'), ('purchase', 'Egreso')], required=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string="Cuenta Analítica")
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string="Etiquetas analíticas")

    


    def button_generar_cuota(self):
       
        if self.monto_cuota<=0:
            raise exceptions.ValidationError('Monto inválido')
        if self.cant_cuotas<=0:
            raise exceptions.ValidationError('Cantidad de cuotas inválida')
        if self.descuento_porcentaje <0:
            raise exceptions.ValidationError('Porcentaje de descuento inválido')

        for i in range(0,self.cant_cuotas):
            c={
                'partner_id':self.partner_id.id,
                'tipo_cuota':self.tipo_cuota,
                'product_id':self.product_id.id,
                'monto_cuota':self.monto_cuota,
                'currency_id':self.currency_id.id,
                'descuento_porcentaje':self.descuento_porcentaje,
                'fecha_vencimiento':self.fecha_vencimiento + relativedelta(months=+(i)),
                'nro_cuota':"%s de %s"%(i+1,self.cant_cuotas),
                'state':'draft',
                'analytic_account_id':self.analytic_account_id.id,
                'analytic_tag_ids':[(6,0,self.analytic_tag_ids.ids)]
            }
            self.env['cuotas.cuota'].create(c)
        return