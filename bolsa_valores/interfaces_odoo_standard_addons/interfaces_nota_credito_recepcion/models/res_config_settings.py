from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    nota_credito_recepcion = fields.Many2one('stock.picking.type',
                                             string="Depósito de recepciones para notas de crédito",
                                             default_model="res.config.settings")

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('nota_credito_recepcion_parameter',
                                                  self.nota_credito_recepcion.id)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            nota_credito_recepcion=int(
                self.env['ir.config_parameter'].sudo().get_param('nota_credito_recepcion_parameter')) or False,
        )
        return res