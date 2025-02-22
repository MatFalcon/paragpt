from ast import literal_eval

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cuenta_ganancia_ids = fields.Many2many('account.account', 'tipo_cuenta_ganancia',
                                           string="Tipo de Cuentas por Ganancia por diferencia de cambios",
                                           default_model='res.config.settings')
    cuenta_perdida_ids = fields.Many2many('account.account', 'tipo_cuenta_perdida',
                                          string="Tipo de Cuentas por Perdida por diferencia de cambios",
                                          default_model='res.config.settings')

    cuenta_perdida_dif_id = fields.Many2one('account.account', string="Cuenta de perdida por diferencia de cambio",
                                            default_model='res.config.settings')
    cuenta_ganancia_dif_id = fields.Many2one('account.account', string="Cuenta de ganancia por diferencia de cambio",
                                             default_model='res.config.settings')

    journal_dif_id = fields.Many2one('account.journal', string="Diario por diferencia de cambio",
                                     default_model='res.config.settings')

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('asiento_dif_cambio.cuenta_ganancia_ids',
                                                         self.cuenta_ganancia_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('asiento_dif_cambio.cuenta_perdida_ids',
                                                         self.cuenta_perdida_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('cuenta_perdida_dif_id', self.cuenta_perdida_dif_id.id)
        self.env['ir.config_parameter'].sudo().set_param('cuenta_ganancia_dif_id', self.cuenta_ganancia_dif_id.id)
        self.env['ir.config_parameter'].sudo().set_param('journal_dif_id', self.journal_dif_id.id)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        with_user = self.env['ir.config_parameter'].sudo()
        cuenta_ganancia_ids = with_user.get_param('asiento_dif_cambio.cuenta_ganancia_ids')
        cuenta_perdida_ids = with_user.get_param('asiento_dif_cambio.cuenta_perdida_ids')
        res.update(cuenta_ganancia_ids=[(6, 0, literal_eval(cuenta_ganancia_ids))] if cuenta_ganancia_ids else False,
                   cuenta_perdida_ids=[(6, 0, literal_eval(cuenta_perdida_ids))] if cuenta_perdida_ids else False,
                   cuenta_ganancia_dif_id=int(
                       self.env['ir.config_parameter'].sudo().get_param('cuenta_ganancia_dif_id')) or False,
                   cuenta_perdida_dif_id=int(
                       self.env['ir.config_parameter'].sudo().get_param('cuenta_perdida_dif_id')) or False,
                   journal_dif_id=int(self.env['ir.config_parameter'].sudo().get_param('journal_dif_id')) or False)

        return res
