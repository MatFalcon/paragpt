from odoo import fields, models, api, exceptions, _


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    rate_tipo_cambio_comprador = fields.Float(
        digits=0,
        group_operator="avg",
        help='The rate of the currency to the currency of rate 1',
        string='Technical Rate'
    )
    company_rate_tipo_cambio_comprador = fields.Float(
        digits=0,
        compute="_compute_company_rate_tipo_cambio_comprador",
        inverse="_inverse_company_rate_tipo_cambio_comprador",
        group_operator="avg",
        help="The currency of rate 1 to the rate of the currency.",
    )
    inverse_company_rate_tipo_cambio_comprador = fields.Float(
        digits=0,
        compute="_compute_inverse_company_rate_tipo_cambio_comprador",
        inverse="_inverse_inverse_company_rate_tipo_cambio_comprador",
        group_operator="avg",
        help="The rate of the currency to the currency of rate 1 ",
    )

    def _get_last_rates_tipo_cambio_comprador_for_companies(self, companies):
        # interfaces_tipo_cambio_compra_venta/models/res_currency_rate.py
        return {
            company: company.currency_id.rate_ids.sudo().filtered(lambda x: (
                    x.rate_tipo_cambio_comprador
                    and x.company_id == company or not x.company_id
            )).sorted('name')[-1:].rate_tipo_cambio_comprador or 1
            for company in companies
        }

    @api.depends('rate_tipo_cambio_comprador', 'name', 'currency_id', 'company_id', 'currency_id.rate_ids.rate_tipo_cambio_comprador')
    @api.depends_context('company')
    def _compute_company_rate_tipo_cambio_comprador(self):
        # interfaces_tipo_cambio_compra_venta/models/res_currency_rate.py
        last_rate = self.env['res.currency.rate']._get_last_rates_tipo_cambio_comprador_for_companies(self.company_id | self.env.company)
        for currency_rate in self:
            company = currency_rate.company_id or self.env.company
            currency_rate.company_rate_tipo_cambio_comprador = (
                                                                       currency_rate.rate_tipo_cambio_comprador or currency_rate._get_latest_rate().rate_tipo_cambio_comprador or 1.0) / \
                                                               last_rate[company]

    @api.onchange('company_rate_tipo_cambio_comprador')
    def _inverse_company_rate_tipo_cambio_comprador(self):
        # interfaces_tipo_cambio_compra_venta/models/res_currency_rate.py
        last_rate = self.env['res.currency.rate']._get_last_rates_tipo_cambio_comprador_for_companies(self.company_id | self.env.company)
        for currency_rate in self:
            company = currency_rate.company_id or self.env.company
            currency_rate.rate_tipo_cambio_comprador = currency_rate.company_rate_tipo_cambio_comprador * last_rate[company]

    @api.depends('company_rate_tipo_cambio_comprador')
    def _compute_inverse_company_rate_tipo_cambio_comprador(self):
        # interfaces_tipo_cambio_compra_venta/models/res_currency_rate.py
        for currency_rate in self:
            if not currency_rate.company_rate_tipo_cambio_comprador:
                currency_rate.company_rate_tipo_cambio_comprador = 1.0
            currency_rate.inverse_company_rate_tipo_cambio_comprador = 1.0 / currency_rate.company_rate_tipo_cambio_comprador

    @api.onchange('inverse_company_rate_tipo_cambio_comprador')
    def _inverse_inverse_company_rate_tipo_cambio_comprador(self):
        # interfaces_tipo_cambio_compra_venta/models/res_currency_rate.py
        for currency_rate in self:
            if not currency_rate.inverse_company_rate_tipo_cambio_comprador:
                currency_rate.inverse_company_rate_tipo_cambio_comprador = 1.0
            currency_rate.company_rate_tipo_cambio_comprador = 1.0 / currency_rate.inverse_company_rate_tipo_cambio_comprador

    def _sanitize_vals(self, vals):
        # interfaces_tipo_cambio_compra_venta/models/res_currency_rate.py
        vals = super(ResCurrencyRate, self)._sanitize_vals(vals)
        if 'inverse_company_rate_tipo_cambio_comprador' in vals and ('company_rate_tipo_cambio_comprador' in vals or 'rate' in vals):
            del vals['inverse_company_rate_tipo_cambio_comprador']
        if 'company_rate_tipo_cambio_comprador' in vals and 'rate' in vals:
            del vals['company_rate_tipo_cambio_comprador']
        return vals

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # interfaces_tipo_cambio_compra_venta/models/res_currency_rate.py
        result = super(ResCurrencyRate, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type in ('tree'):
            names = {
                'company_currency_name': (self.env['res.company'].browse(self._context.get('company_id')) or self.env.company).currency_id.name,
                'rate_currency_name': self.env['res.currency'].browse(self._context.get('active_id')).name or 'Unit',
            }
            doc = etree.XML(result['arch'])
            for field in [
                ['company_rate', _('%(rate_currency_name)s por %(company_currency_name)s Vendedor', **names)],
                ['inverse_company_rate', _('%(company_currency_name)s por %(rate_currency_name)s Vendedor', **names)],
                ['company_rate_tipo_cambio_comprador', _('%(rate_currency_name)s por %(company_currency_name)s Comprador', **names)],
                ['inverse_company_rate_tipo_cambio_comprador', _('%(company_currency_name)s por %(rate_currency_name)s Comprador', **names)],
            ]:
                node = doc.xpath("//tree//field[@name='%s']" % field[0])
                if node:
                    node[0].set('string', field[1])
            result['arch'] = etree.tostring(doc, encoding='unicode')
        return result
