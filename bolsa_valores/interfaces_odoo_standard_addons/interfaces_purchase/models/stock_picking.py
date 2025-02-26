from odoo import api, fields, models, exceptions, _
from datetime import date


class StockPicking(models.AbstractModel):
    _inherit = 'stock.picking'

    def action_generar_reporte_costos_xls(self):
        datas = {
            # 'active_id': self.env.context.get('active_ids', [])
            'active_id': self.id
        }
        return self.env.ref('interfaces_purchase.action_areport_costo_importacion').report_action(self, data=datas)
