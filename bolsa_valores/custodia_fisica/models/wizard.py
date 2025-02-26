from odoo import api, exceptions, fields, models


class WizardFacturar(models.TransientModel):
    _name = 'custodia_fisica.wizard.facturar'
    _description = 'Wizard facturar'

    journal_id = fields.Many2one('account.journal', string="Diario", domain=[
                                 ('type', '=', 'sale')], required=True)
    estado_factura = fields.Selection(string="Estado de factura/s",
                                      help="Estado con el que la/s factura/s deben ser creada/s",
                                      selection=[('draft', 'Borrador'),
                                                 ('posted', 'Publicado')],
                                      default='draft', required=True)
    fecha_factura = fields.Date(string="Fecha de factura/s",
                                help="Si no se elige una fecha, todas las facturas serán creadas al día de hoy")
    custodia_fisica_ids = fields.Many2many(
        'custodia_fisica.custodia_fisica', relation='crear_factura_custodia_fisica_wizard', string="Emisiones y Custodia")

    @api.depends('custodia_fisica_ids', 'journal_id', 'estado_factura')
    def button_generar_factura(self):
        try:
            facturas = self.custodia_fisica_ids.action_facturar(
                self.journal_id, self.estado_factura, self.fecha_factura)

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


class WizardCrearCustodias(models.TransientModel):
    _name = 'custodia_fisica.wizard.crear_custodias'
    _description = 'Wizard Crear Custodias'

    custodia_fisica_line_ids = fields.Many2many(
        'custodia_fisica.custodia_fisica_line', relation='crear_custodias_custodia_line_wizard', string="Lineas de Custodias")

    def button_generar_custodia(self):
        try:
            custodias = self.custodia_fisica_line_ids.action_crear_custodia()

            return {
                'name': 'Custodia Generada',
                'view_mode': 'tree,form',
                'res_model': 'custodia_fisica.custodia_fisica',
                # 'view_id': view_id.id,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', custodias)],
            }
        except Exception as e:
            print(e)
            raise exceptions.ValidationError(e)
