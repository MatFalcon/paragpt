from odoo import api, fields, models, exceptions


class AccountMove(models.Model):
    _inherit = 'account.move'

    es_factura_exterior = fields.Boolean(string='Es Factura Exterior', default=False)
    es_despacho_importacion = fields.Boolean(string='Es un Despacho de importación', default=False)
    importacion_factura_compra_ids = fields.Many2many('account.move', 'account_move_importacion_account_move', 'account_move_master', 'account_move_helper',
                                                      string='Factura Importación', domain=[
            ('es_factura_exterior', '=', True),
            ('state', '=', 'posted'),
            ('move_type', '=', 'in_invoice'),
        ])

    def write(self, vals):
        # interfaces_iva_importacion/models/account_move.py
        res = super(AccountMove, self).write(vals)
        if any(self.mapped('es_factura_exterior')) and self.mapped('invoice_line_ids.tax_ids') and any(self.mapped('invoice_line_ids.tax_ids.amount')):
            raise exceptions.ValidationError('Una Factura Exterior (Importación) solo debe tener Exentas como impuestos')
        return res

    def get_tipo_identificacion(self):
        # interfaces_iva_importacion/models/account_move.py
        result = super(AccountMove, self).get_tipo_identificacion()
        if self.es_despacho_importacion:
            result = 17
        return result

    def get_identificacion(self):
        # interfaces_iva_importacion/models/account_move.py
        identificacion = super(AccountMove, self).get_identificacion()
        if self.es_despacho_importacion:
            identificacion = self.importacion_factura_compra_ids.mapped('partner_id').vat

            if identificacion and len(identificacion.split('-')) > 1:
                identificacion = identificacion.split('-')[0]
        return identificacion if identificacion else '44444401'

    def get_nombre_partner(self):
        # interfaces_iva_importacion/models/account_move.py
        result = super(AccountMove, self).get_nombre_partner()
        if self.es_despacho_importacion:
            result = self.importacion_factura_compra_ids.mapped('partner_id').name
        return result

    def get_timbrado(self):
        # interfaces_iva_importacion/models/account_move.py
        result = super(AccountMove, self).get_timbrado()
        if self.es_despacho_importacion:
            result = 0
        return result

    def get_monto10(self):
        # interfaces_iva_importacion/models/account_move.py
        result = super(AccountMove, self).get_monto10()
        if self.es_despacho_importacion:
            result = 11 * sum(line.price_subtotal for line in self.invoice_line_ids.filtered(lambda x: x.account_id.es_cuenta_iva_importacion))
        return result

    def get_monto_exento(self):
        # interfaces_iva_importacion/models/account_move.py
        result = super(AccountMove, self).get_monto_exento()
        if self.es_despacho_importacion:
            result = 0
        return result

    def get_monto_total(self):
        # interfaces_iva_importacion/models/account_move.py
        result = super(AccountMove, self).get_monto_total()
        if self.es_despacho_importacion:
            result = self.get_monto10()
        return result

    def get_operacion_moneda_extranjera(self):
        # interfaces_iva_importacion/models/account_move.py
        result = super(AccountMove, self).get_operacion_moneda_extranjera()
        if self.es_despacho_importacion:
            result = 'S'
        return result
