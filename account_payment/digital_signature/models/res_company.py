from odoo import models, fields, api

class Company(models.Model):
    _inherit = "res.company"
    
    firma = fields.Char(string="Firma Digital", default="Sin Firma")
    
    # Relación con purchase.order para poder acceder al campo digital_sign
    purchase_order_id = fields.Many2one(
        'purchase.order', 
        string="Orden de Compra",
        help="Orden de compra asociada para obtener la firma digital."
    )

    # Campo relacionado que trae el valor de digital_sign desde purchase.order
    digital_sign = fields.Binary(
        string="Firma Digital",
        related='purchase_order_id.digital_sign',
        readonly=False,
        store=True,
        help="Firma digital obtenida desde la orden de compra."
    )

    sign_by = fields.Text(
        string="Firmado por",
        related='purchase_order_id.sign_by',
        readonly=False,
        store=True,
        help="Nombre del firmante obtenido desde la orden de compra."
    )

    @api.onchange('digital_sign', 'sign_by')
    def _onchange_digital_sign(self):
        if self.digital_sign:
            self.firma = self.digital_sign
        elif self.sign_by:
            self.firma = self.sign_by
        else:
            self.firma = " "