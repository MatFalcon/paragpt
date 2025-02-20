from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class PresaleCurrencyRate(models.Model):
    _name = 'presale.currency_rate'
    _description = 'Presale currency rates'

    team_id = fields.Many2one('crm.team',string="Team", tracking=True, copy=True)
    name = fields.Date(string="Date", tracking=True, copy=True)
    currency_id = fields.Many2one('res.currency','Currency', tracking=True, copy=True)
    rate = fields.Float(string="Rate", tracking=True, copy=True)

    @api.constrains('name','currency_id')
    def _check_currency_rate(self):
        for rec in self:
            currency_rates = self.env['presale.currency_rate'].search_count([('currency_id','=',rec.currency_id.id),('name','=',rec.name)])
            if currency_rates > 1:
                raise ValidationError(_('A rate already exist for this currency on the selected date'))


