from odoo import fields, models, api, exceptions, _, release
from lxml import etree


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # interfaces_tipo_cambio_compra_venta/models/res_currency.py
        result = super(ResCurrency, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if release.major_version != '15.0':
            return result
        if view_type in ('tree', 'form'):
            currency_name = (self.env['res.company'].browse(self._context.get('company_id')) or self.env.company).currency_id.name
            doc = etree.XML(result['arch'])
            for field in [
                ['company_rate', _('Unidad por %s Vendedor', currency_name)],
                ['inverse_company_rate', _('%s por Unidad Vendedor', currency_name)],
                ['company_rate_tipo_cambio_comprador', _('Unidad por %s Comprador', currency_name)],
                ['inverse_company_rate_tipo_cambio_comprador', _('%s por Unidad Comprador', currency_name)]
            ]:
                node = doc.xpath("//tree//field[@name='%s']" % field[0])
                if node:
                    node[0].set('string', field[1])
            result['arch'] = etree.tostring(doc, encoding='unicode')
        return result

    @api.model
    def _get_view(self, view_id=None, view_type='form', **options):
        # interfaces_tipo_cambio_compra_venta/models/res_currency.py
        result = super(ResCurrency, self)._get_view(view_id=view_id, view_type=view_type, **options)
        if release.major_version != '16.0':
            return result
        arch, view = super()._get_view(view_id, view_type, **options)
        if view_type in ('tree', 'form'):
            currency_name = (self.env['res.company'].browse(self._context.get('company_id')) or self.env.company).currency_id.name
            for field in [
                ['company_rate', _('Unidad por %s Vendedor', currency_name)],
                ['inverse_company_rate', _('%s por Unidad Vendedor', currency_name)],
                ['company_rate_tipo_cambio_comprador', _('Unidad por %s Comprador', currency_name)],
                ['inverse_company_rate_tipo_cambio_comprador', _('%s por Unidad Comprador', currency_name)]
            ]:
                node = arch.xpath("//tree//field[@name='%s']" % field[0])
                if node:
                    node[0].set('string', field[1])
        return arch, view

    def _convert_tipo_cambio_vendedor(self, from_amount, to_currency, company, date, round=True, force_rate=False):
        # interfaces_tipo_cambio_compra_venta/models/res_currency.py
        """Returns the converted amount of ``from_amount``` from the currency
           ``self`` to the currency ``to_currency`` for the given ``date`` and
           company.

           :param company: The company from which we retrieve the convertion rate
           :param date: The nearest date from which we retriev the conversion rate.
           :param round: Round the result or not
        """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"
        # apply conversion rate
        conversion_rate = self._get_conversion_rate_tipo_cambio_vendedor(self, to_currency, company, date)
        if force_rate:
            conversion_rate = force_rate
            if self == company.currency_id:
                conversion_rate = 1 / force_rate
        if self == to_currency:
            to_amount = from_amount
        else:
            to_amount = from_amount * conversion_rate
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount

    def _convert_tipo_cambio_comprador(self, from_amount, to_currency, company, date, round=True, force_rate=False):
        # interfaces_tipo_cambio_compra_venta/models/res_currency.py
        """Returns the converted amount of ``from_amount``` from the currency
           ``self`` to the currency ``to_currency`` for the given ``date`` and
           company.

           :param company: The company from which we retrieve the convertion rate
           :param date: The nearest date from which we retriev the conversion rate.
           :param round: Round the result or not
        """
        self, to_currency = self or to_currency, to_currency or self
        assert self, "convert amount from unknown currency"
        assert to_currency, "convert amount to unknown currency"
        assert company, "convert amount from unknown company"
        assert date, "convert amount from unknown date"
        # apply conversion rate
        conversion_rate = self._get_conversion_rate_tipo_cambio_comprador(self, to_currency, company, date)
        if force_rate:
            conversion_rate = force_rate
            if self == company.currency_id:
                conversion_rate = 1 / force_rate
        if self == to_currency:
            to_amount = from_amount
        else:
            to_amount = from_amount * conversion_rate
        # apply rounding
        return to_currency.round(to_amount) if round else to_amount

    def _get_rates_tipo_cambio_comprador(self, company, date):
        # interfaces_tipo_cambio_compra_venta/models/res_currency.py
        if not self.ids:
            return {}
        self.env['res.currency.rate'].flush(['rate_tipo_cambio_comprador', 'currency_id', 'company_id', 'name'])
        query = """SELECT c.id,
                          COALESCE((SELECT r.rate_tipo_cambio_comprador FROM res_currency_rate r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS rate_tipo_cambio_comprador
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company.id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        return currency_rates

    @api.model
    def _get_conversion_rate_tipo_cambio_comprador(self, from_currency, to_currency, company, date):
        # interfaces_tipo_cambio_compra_venta/models/res_currency.py
        currency_rates = (from_currency + to_currency)._get_rates_tipo_cambio_comprador(company, date)
        res = currency_rates.get(to_currency.id) / currency_rates.get(from_currency.id)
        return res

    @api.model
    def _get_conversion_rate_tipo_cambio_vendedor(self, from_currency, to_currency, company, date):
        # interfaces_tipo_cambio_compra_venta/models/res_currency.py
        return self._get_conversion_rate(from_currency=from_currency, to_currency=to_currency, company=company, date=date)
