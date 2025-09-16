# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.tools import float_compare
from datetime import date
import logging

_logger = logging.getLogger(__name__)
class StockLot(models.Model):
    _inherit = "stock.lot"

    is_taken = fields.Boolean(string='Taken lot', default=False,
                              help='If enables this lot number is taken')



    @api.model
    def get_available_locations_for_product(self, product_id):
        """Obtiene las ubicaciones disponibles para un producto en el POS"""
        print("ENTRA EN get_available_locations_for_product")
        pos_config = self.env['pos.config'].search([('active', '=', True)], limit=1)
        if not pos_config:
            return []
        print("POS_COFIG", pos_config)
        # Obtener ubicaciones permitidas para este POS
        allowed_locations = pos_config.picking_type_id.default_location_src_id
        print("UBICACIONES DISPONIBLES", allowed_locations)
        child_locations = self.env['stock.location'].search([
            ('location_id', 'child_of', allowed_locations.id),
            ('usage', '=', 'internal')
        ])
        
        # Buscar quants con stock > 0 en estas ubicaciones
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product_id),
            ('location_id', 'in', child_locations.ids),
            ('quantity', '>', 0)
        ])
        print("SERIES O LOTES CON UNDIADES", quants)
        
        locations_with_stock = []
        for location in child_locations:
            location_quants = quants.filtered(lambda q: q.location_id.id == location.id)
            if location_quants:
                total_qty = sum(location_quants.mapped('quantity'))
                locations_with_stock.append({
                    'id': location.id,
                    'name': location.complete_name,
                    'available_qty': total_qty
                })
        print("UBUCACIONES DISPONIBLES", len(locations_with_stock))
        return locations_with_stock

    @api.model
    def get_lots_by_location_and_product(self, product_id, location_id):
        """Obtiene lotes disponibles por ubicación y producto"""
        today = date.today()
        
        # Buscar quants en la ubicación específica
        quants = self.env['stock.quant'].search([
            ('product_id', '=', product_id),
            ('location_id', '=', location_id),
            ('quantity', '>', 0),
            ('lot_id', '!=', False)
        ])
        
        lots_data = []
        for quant in quants:
            lot = quant.lot_id
            if lot and not lot.is_taken:
                # Verificar fecha de vencimiento
                is_valid = True
                if lot.use_date and lot.use_date.date() < today:
                    is_valid = False
                    
                lots_data.append({
                    'id': lot.id,
                    'name': lot.name,
                    'available_qty': quant.quantity,
                    'expiration_date': lot.use_date.strftime('%d/%m/%Y') if lot.use_date else '',
                    'is_valid': is_valid,
                    'location_name': quant.location_id.name
                })
        
        # Ordenar por fecha de vencimiento (FEFO)
        lots_data.sort(key=lambda x: x.get('expiration_date', ''))
        return lots_data

    @api.model
    def propose_lot_assignment(self, product_id, requested_qty, preferred_locations=None):
        """Propone asignación automática de lotes basada en FEFO"""
        if not preferred_locations:
            locations = self.get_available_locations_for_product(product_id)
            preferred_locations = [loc['id'] for loc in locations]
        
        assignment_proposal = []
        remaining_qty = requested_qty
        
        for location_id in preferred_locations:
            if remaining_qty <= 0:
                break
                
            lots = self.get_lots_by_location_and_product(product_id, location_id)
            valid_lots = [lot for lot in lots if lot['is_valid']]
            
            for lot in valid_lots:
                if remaining_qty <= 0:
                    break
                    
                available_qty = lot['available_qty']
                qty_to_assign = min(remaining_qty, available_qty)
                
                assignment_proposal.append({
                    'lot_id': lot['id'],
                    'lot_name': lot['name'],
                    'location_id': location_id,
                    'location_name': lot['location_name'],
                    'qty_assigned': qty_to_assign,
                    'expiration_date': lot['expiration_date']
                })
                
                remaining_qty -= qty_to_assign
        
        return {
            'assignment': assignment_proposal,
            'fully_covered': remaining_qty <= 0,
            'remaining_qty': remaining_qty
        }