from odoo import api, exceptions, fields, models


class WizardFacturar(models.TransientModel):
    _name = 'emisiones.wizard.facturar'
    _description = 'Wizard facturar'

    journal_id = fields.Many2one('account.journal', string="Diario", domain=[('type', '=', 'sale')], required=True)
    estado_factura = fields.Selection(string="Estado de factura/s",
                                      help="Estado con el que la/s factura/s deben ser creada/s",
                                      selection=[('draft', 'Borrador'), ('posted', 'Publicado')],
                                      default='draft', required=True)
    fecha_factura = fields.Date(string="Fecha de factura/s",
                                help="Si no se elige una fecha, todas las facturas serán creadas al día de hoy")
    emisiones_ids = fields.Many2many('emisiones.emisiones_custodia', string="Emisiones y Custodia")

    @api.depends('emisiones_ids', 'journal_id', 'estado_factura')
    def button_generar_factura(self):
        try:
            view_id = self.env.ref('account.view_out_invoice_tree')
            facturas = self.emisiones_ids.action_facturar(self.journal_id, self.estado_factura, self.fecha_factura)

            return {
                'name': 'Facturas generadas',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', facturas)],
            }
        except Exception as e:
            print(e)
            raise exceptions.ValidationError(e)
