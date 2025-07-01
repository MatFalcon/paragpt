from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    es_impresora = fields.Boolean(string="Es una impresora")
    
    accessorio_ids = fields.Many2many(
        'product.template',
        'product_template_accessory_rel',
        'product_template_id',
        'accessory_template_id',
        string="Accesorios",
        #domain="[('es_accesorio', '=', True)]",
        help="Lista de accesorios compatibles con esta impresora"
    )

    es_accesorio = fields.Boolean(string="Es un accesorio")

    impresora_compatible_ids = fields.Many2many(
        'product.template',
        'product_template_compatible_rel',
        'accessory_template_id',
        'product_template_id',
        string="Impresoras compatibles",
        #domain="[('es_impresora', '=', True)]",
        help="Lista de impresoras compatibles con este accesorio"
    )



    @api.model_create_multi
    def create(self, vals_list):
        """
        Crea nuevos productos plantilla y actualiza las relaciones bidireccionales
        entre impresoras y accesorios según los valores definidos en la creación.
        """
        records = super().create(vals_list)
        for record in records:
            record._update_bidirectional_relations()
        return records

    def write(self, vals):
        """
        Al escribir (actualizar) productos plantilla, actualiza las relaciones 
        bidireccionales entre impresoras y accesorios para mantener coherencia.
        """
        res = super().write(vals)
        self._update_bidirectional_relations()
        return res

    def _update_bidirectional_relations(self):
        """
        Asegura que las relaciones entre impresoras y accesorios sean
        sincronizadas en ambas direcciones (impresora -> accesorio y viceversa).
        """
        for rec in self:
            for acc in rec.accessorio_ids:
                if rec.id not in acc.impresora_compatible_ids.ids:
                    acc.impresora_compatible_ids = [(4, rec.id)]
            for impresora in rec.impresora_compatible_ids:
                if rec.id not in impresora.accessorio_ids.ids:
                    impresora.accessorio_ids = [(4, rec.id)]

    @api.onchange('es_impresora')
    def _onchange_es_impresora(self):
        if self.es_impresora:
            self.es_accesorio = False
        if not self.es_impresora and self.accessorio_ids:
            self.es_impresora = True
            return {
                'warning': {
                    'title': 'Accion no permitida',
                    'message': 'No puedes desactivar "Es impresora" mientras tenga accesorios relacionados. Elimina primero los accesorios.'
                }
            }

    @api.onchange('es_accesorio')
    def _onchange_es_accesorio(self):
        if self.es_accesorio:
            self.es_impresora = False
        if not self.es_accesorio and self.impresora_compatible_ids:
            self.es_accesorio = True
            return {
                'warning': {
                    'title': 'Accion no permitida',
                    'message': 'No puedes desactivar "Es accesorio" mientras tenga impresoras compatibles relacionadas. Elimina primero las impresoras.'
                }
            }

    @api.onchange('accessorio_ids')
    def _onchange_accessorio_ids(self):
        accesorios_actuales = self.accessorio_ids
        for accesorio in accesorios_actuales:
            if accesorio.es_impresora:
                raise ValidationError("No puedes seleccionar otra impresora como accesorio.")
            accesorio.es_accesorio = True
            if self.id and self.id not in accesorio.impresora_compatible_ids.ids:
                accesorio.impresora_compatible_ids |= self
        if self._origin:
            accesorios_antes = self._origin.accessorio_ids
            desvinculados = accesorios_antes - accesorios_actuales
            for accesorio in desvinculados:
                accesorio.impresora_compatible_ids -= self

    # trate de desvincular tmb los accesorios de la impresora si elimino la impresora compatible del accesorio pero off
    @api.onchange('impresora_compatible_ids')
    def _onchange_impresora_compatible_ids(self):
        impresoras_actuales = self.impresora_compatible_ids
        for impresora in impresoras_actuales:
            if impresora.es_accesorio:
                raise ValidationError("No puedes seleccionar un accesorio como impresora compatible.")
            impresora.es_impresora = True
            if self.id and self.id not in impresora.accessorio_ids.ids:
                impresora.accessorio_ids |= self
        if self._origin:
            impresoras_antes = self._origin.impresora_compatible_ids
            desvinculadas = impresoras_antes - impresoras_actuales
            for impresora in desvinculadas:
                impresora.accessorio_ids -= self

    @api.constrains('accessorio_ids')
    def _check_accessorio_ids(self):
        for rec in self:
            for accesorio in rec.accessorio_ids:
                if accesorio.es_impresora:
                    raise ValidationError("No puedes seleccionar otra impresora como accesorio.")
                accesorio.write({'es_accesorio': True})
                if rec.id and rec.id not in accesorio.impresora_compatible_ids.ids:
                    accesorio.impresora_compatible_ids = [(4, rec.id)]
            accesorios_antes = rec._origin.accessorio_ids if rec._origin else self.env['product.template']
            desvinculados = accesorios_antes - rec.accessorio_ids
            for accesorio in desvinculados:
                accesorio.impresora_compatible_ids = [(3, rec.id)]

    @api.constrains('impresora_compatible_ids')
    def _check_impresora_compatible_ids(self):
        for rec in self:
            for impresora in rec.impresora_compatible_ids:
                if impresora.es_accesorio:
                    raise ValidationError("No puedes seleccionar un accesorio como impresora compatible.")
                impresora.write({'es_impresora': True})
                if rec.id and rec.id not in impresora.accessorio_ids.ids:
                    impresora.accessorio_ids = [(4, rec.id)]
            impresoras_antes = rec._origin.impresora_compatible_ids if rec._origin else self.env['product.template']
            desvinculadas = impresoras_antes - rec.impresora_compatible_ids
            for impresora in desvinculadas:
                impresora.accessorio_ids = [(3, rec.id)]

    @api.constrains('es_impresora', 'accessorio_ids')
    def _check_no_desactivar_impresora_con_accesorios(self):
        for rec in self:
            if not rec.es_impresora and rec.accessorio_ids:
                raise ValidationError('No puedes desactivar "Es impresora" mientras tenga accesorios relacionados. Elimina primero los accesorios.')

    @api.constrains('es_accesorio', 'impresora_compatible_ids')
    def _check_no_desactivar_accesorio_con_impresoras(self):
        for rec in self:
            if not rec.es_accesorio and rec.impresora_compatible_ids:
                raise ValidationError('No puedes desactivar "Es accesorio" mientras tenga impresoras compatibles relacionadas. Elimina primero las impresoras.')



class StockProductionLotInherit(models.Model):

    _inherit = 'stock.production.lot'
    
    reservado_preventas = fields.Boolean(compute='_compute_reservado_preventas', store=True)

    # Relacion con linea de preventa (impresora)
    presale_item_ids = fields.One2many(
        'presale.ricoh.order.item', 'serie_id', string='Preventas como Impresora')
    # Relacion con detalles de preventa (accesorio)
    presale_item_detail_ids = fields.One2many(
        'presale.ricoh.order.item.detail', 'serie_id', string='Preventas como Accesorio')

    # Lotes de accesorios relacionados (si es impresora)
    presale_accesorio_lot_ids = fields.Many2many(
        'stock.production.lot', compute='_compute_presale_accesorio_lot_ids', string='Lotes de Accesorios Relacionados')
    # Lote de impresora asociada (si es accesorio)
    presale_impresora_lot_ids = fields.Many2many(
        'stock.production.lot', compute='_compute_presale_impresora_lot_ids', string='Lote de Impresora Relacionada')
    tipo_product = fields.Char(compute="_compute_tipo_product")
    
    @api.depends("product_id")
    def _compute_tipo_product(self):
        """
            Sete a un campo auxiliar que ayuda a la visualizacion de los botones de acceso directo en las series.
        """
        for record in self:
            if record.product_id.es_impresora:
                    record.tipo_product = 'impre'
            elif record.product_id.es_accesorio:
                record.tipo_product = 'acce'
            else:
                record.tipo_product = False     
            
    @api.depends('presale_item_ids')
    def _compute_presale_accesorio_lot_ids(self):
        for lot in self:
            lotes = self.env['stock.production.lot']
            for item in lot.presale_item_ids:
                for detail in item.item_detail_ids:
                    if detail.serie_id:
                        lotes |= detail.serie_id
            lot.presale_accesorio_lot_ids = lotes

    @api.depends('presale_item_detail_ids')
    def _compute_presale_impresora_lot_ids(self):
        for lot in self:
            lotes = self.env['stock.production.lot']
            for detail in lot.presale_item_detail_ids:
                if detail.item_id and detail.item_id.serie_id:
                    lotes |= detail.item_id.serie_id
            lot.presale_impresora_lot_ids = lotes

    @api.depends('presale_item_ids', 'presale_item_detail_ids')
    def _compute_reservado_preventas(self):
        for lot in self:
            lot.reservado_preventas = bool(lot.presale_item_ids or lot.presale_item_detail_ids)

    # Accion: ver linea de preventa (impresora) o detalles (accesorio)
    def action_view_presale_lines(self):
        self.ensure_one()
        if self.product_id and getattr(self.product_id, 'es_impresora', False):
            # Es impresora: mostrar lineas de preventa
            return {
                'type': 'ir.actions.act_window',
                'name': 'Lineas de Preventa',
                'res_model': 'presale.ricoh.order.item',
                'view_mode': 'tree,form',
                'domain': [('serie_id', '=', self.id)],
            }
        else:
            # Es accesorio: mostrar detalles de preventa
            return {
                'type': 'ir.actions.act_window',
                'name': 'Detalles de Preventa',
                'res_model': 'presale.ricoh.order.item.detail',
                'view_mode': 'tree,form',
                'domain': [('serie_id', '=', self.id)],
            }

    # ver lotes relacionados (accesorios si es impresora, impresora si es accesorio)
    def action_view_related_lots(self):
        self.ensure_one()
        if self.product_id and getattr(self.product_id, 'es_impresora', False):
            # Es impresora: mostrar lotes de accesorios relacionados
            return {
                'type': 'ir.actions.act_window',
                'name': 'Lotes de Accesorios Relacionados',
                'res_model': 'stock.production.lot',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.presale_accesorio_lot_ids.ids)],
            }
        else:
            # Es accesorio: mostrar lote de impresora asociada
            return {
                'type': 'ir.actions.act_window',
                'name': 'Lote de Impresora Relacionada',
                'res_model': 'stock.production.lot',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', self.presale_impresora_lot_ids.ids)],
            }
    