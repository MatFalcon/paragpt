from ast import literal_eval

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    product_gastos_administrativos_id = fields.Many2one('product.product', string="Producto de Gastos Administrativos",
                                         default_model='res.config.settings')

    product_transferencia_cartera_id = fields.Many2one('product.product', string="Producto de Transferencia de Cartera",
                                                        default_model='res.config.settings')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('product_gastos_administrativos_id', self.product_gastos_administrativos_id.id)
        self.env['ir.config_parameter'].sudo().set_param('product_transferencia_cartera_id', self.product_transferencia_cartera_id.id)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(product_gastos_administrativos_id= int(self.env['ir.config_parameter'].sudo().get_param('product_gastos_administrativos_id')) or False,
                   product_transferencia_cartera_id= int(self.env['ir.config_parameter'].sudo().get_param('product_transferencia_cartera_id')) or False,)

        return res

