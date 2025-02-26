from odoo import api, fields, models,exceptions


class WizardFacturar(models.TransientModel):
    _name = 'cuotas.wizard.facturar'
    _description = 'Wizard facturar'

    journal_id=fields.Many2one('account.journal',string="Diario", domain=[('type','in',['sale','purchase'])],required=True)
    estado_factura=fields.Selection(string="Estado de factura/s",help="Estado con el que la/s factura/s deben ser creada/s",selection=[('draft','Borrador'),('posted','Publicado')],default='draft',required=True)
    fecha_factura=fields.Date(string="Fecha de factura/s",help="Si no se elige una fecha, todas las facturas serán creadas al día de hoy")
    cuotas_ids=fields.Many2many('cuotas.cuota',string="Cuotas")
    tipo_cuota = fields.Selection(string="Tipo de cuota", selection=[(
        'sale', 'Ingreso'), ('purchase', 'Egreso')], required=True)
    
    @api.depends('cuotas_ids','journal_id','estado_factura')
    def button_generar_factura(self):
    
        view_id=self.env.ref('account.view_out_invoice_tree')
        if any(self.cuotas_ids.filtered(lambda x:x.state!='confirmado')):
            raise exceptions.ValidationError('No se pueden facturar cuotas que no estén confirmadas')
        if any(self.cuotas_ids.filtered(lambda x:not x.partner_id)):
            raise exceptions.ValidationError('Algunas de las facturas seleccionadas no tienen asignado una empresa')
        
        facturas=self.cuotas_ids.action_facturar(self.journal_id,self.estado_factura,self.fecha_factura)
           
        return {
            'name':'Facturas generadas',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id','in',facturas)],
        }
