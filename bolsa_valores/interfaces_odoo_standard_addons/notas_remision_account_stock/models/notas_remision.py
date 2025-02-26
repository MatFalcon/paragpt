from odoo import _, api, fields, models,exceptions

class NotasRemision(models.Model):
    _inherit = 'notas_remision_account.nota.remision'

    estirar_desde=fields.Selection(string="Estirar lineas desde",selection=[('envios','Envios'),('facturas','Facturas')],default='envios',tracking=True)
    picking_ids=fields.Many2many('stock.picking',string='Envios',copy=False,tracking=True)

    @api.depends('estirar_desde','picking_ids','invoice_id')
    def action_cargar_productos(self):
        
        self.delete_lines()
        new_lines=[]
        if self.estirar_desde=='facturas':
            for line in self.invoice_id.invoice_line_ids:
                l={
                    'product_id':line.product_id.id,
                    'name':line.name,
                    'qty':line.quantity,
                    'uom_id':line.product_uom_id.id
                }
                new_lines.append((0,0,l))
        elif self.estirar_desde=='envios':
            for picking in self.picking_ids:
                for line in picking.move_line_ids:
                    l={
                        'product_id':line.product_id.id,
                        'name':line.product_id.display_name,
                        'qty':line.qty_done,
                        'uom_id':line.product_uom_id.id
                    }
                    new_lines.append((0,0,l))
        else:
            new_lines=[]

        self.write({'line_ids':new_lines})

    def button_confirmar(self):
        res=super(NotasRemision,self).button_confirmar()
        for i in self:
            if i.picking_ids:
                i.picking_ids.write({'nota_remision_id':i.id})
        return res
    
    def button_cancelar(self):
        res=super(NotasRemision,self).button_cancelar()
        for i in self:
            if i.picking_ids:
                i.picking_ids.write({'nota_remision_id':False})
        return res
    
    @api.onchange('estirar_desde')
    def onchange_estirar_desde(self):
        if self.estirar_desde=='facturas':
            self.picking_ids=False
        self.action_cargar_productos()

    @api.onchange('invoice_id')
    def onchange_invoice(self):
        self.action_cargar_productos()
    
    @api.onchange('picking_ids')
    def onchange_pickings(self):
        self.action_cargar_productos()