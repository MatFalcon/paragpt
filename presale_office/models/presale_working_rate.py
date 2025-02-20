from odoo import fields, models, api,_
from odoo.exceptions import ValidationError


class PresaleWorkingRate(models.Model):
    _name = 'presale.working_rate'
    _description = 'Presale working rates'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']

    # name = fields.Date(string="Date", track_visibility='onchange')
    team_id = fields.Many2one('crm.team','Team', tracking=True, copy=True)
    labor_type_id = fields.Many2one('presale.labor_type','Labor type', tracking=True, copy=True)
    rate = fields.Float(string="Rate", tracking=True, copy=True)
    effective_date = fields.Date(string="Effective Date", copy=True)

    #TODO
    # Remove or upadte filter function -> add date to differentiate from many updates rates

    @api.constrains('team_id','labor_type_id','effective_date')
    def _check_working_rate(self):
        for rec in self:
            currency_rates = self.env['presale.working_rate'].search_count([('team_id','=',rec.team_id.id),('labor_type_id','=',rec.labor_type_id.id),
                                                                            ('effective_date', '=', rec.effective_date)])
            if currency_rates > 1:
                raise ValidationError(_('A previously used rate already exists based on currency and type of labor!'))


