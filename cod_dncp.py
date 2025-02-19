from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CodDNCP(models.Model):
    _name = "cod.dncp.account.move.line"
    name = fields.Char()
    cantidad = fields.Integer()
    move_id = fields.Many2one('account.move', ondelete="cascade",
                              help="Cod DNCP de los productos")
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Product'
    )
    cod_dncp_nivel_general = fields.Char("Cod. DNCP-Nivel General")
    cod_dncp_nivel_especifico = fields.Char("Cod. DNCP-Nivel Especifico")