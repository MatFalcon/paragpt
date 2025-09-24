# -*- coding: utf-8 -*-

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    lista_precio_mantenimiento_ids = fields.Many2one(
        'mantenimiento_registro.lista_precios',
        string="Lista de precios de mantenimiento",
        copy=False
    )

    # TODO: Borrar este codigo luego, es para la version manual de la lista de precios
    # @api.onchange('lista_precio_mantenimiento_ids')
    # def _onchange_lista_precio_mantenimiento_ids(self):
    #     for record in self:
    #         if record.lista_precio_mantenimiento_ids:
    #             record.price_unit = record.lista_precio_mantenimiento_ids.monto

    @api.onchange('product_id')
    def _onchange_product_id_custom(self):
        super(AccountMoveLine, self)._onchange_product_id()
        for record in self:
            record.update_unit_price()

    @api.onchange('product_uom_id')
    def _onchange_uom_id(self):
        ''' Recompute the 'price_unit' depending of the unit of measure. '''
        super(AccountMoveLine, self)._onchange_uom_id()
        for record in self:
            record.update_unit_price()

    def update_unit_price(self):
        try:
            for record in self:
                ts = record.partner_id.tipo_sociedad
                rango_capital = record.partner_id.capital

                # Si tenemos un producto que es de mantenimiento de registros
                if record.product_id.es_mantenimiento_registro:

                    # Obtenemos la lista de precios que corresponde al tipo de sociedad y al rango de capital
                    lista_precios = self.env['mantenimiento_registro.lista_precios'].search(
                        [('tipo_sociedad', '=', ts), ('desde', '<=', rango_capital), ('hasta', '>=', rango_capital)]
                    )

                    if lista_precios:
                        # Si hay una lista de precios, la asignamos a la línea
                        record.lista_precio_mantenimiento_ids = lista_precios.id
                        # Y ponemos el precio unitario como el monto de la lista de precios
                        self.price_unit = lista_precios.monto

                elif record.product_id.jornal:
                    # Si tiene jornal, lo ponemos como precio unitario
                    record.price_unit = record.product_id.jornal.monto
        except Exception as e:
            print(e)
            print("Error")
