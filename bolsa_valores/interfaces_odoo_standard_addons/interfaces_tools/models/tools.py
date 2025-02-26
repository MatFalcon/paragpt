from odoo import api, fields, models,exceptions
from .amount_to_text import to_word


class Tools(models.Model):
    _name = 'interfaces_tools.tools'
    _description = 'Tool'

    @api.model
    def format_amount(self, monto, currency=False, lang=False):
        if not lang:
            lang_str = self._context.get('lang')
        else:
            lang_str = lang
        if not currency:
            currency_id = self.env.user.company_id.currency_id
        else:
            currency_id = currency
        lang_id = self.env['res.lang'].search([('code', '=', lang_str)])

        if lang_id and currency_id:
            fmt = "%.{0}f".format(currency_id.decimal_places)
            return lang_id.format(fmt, monto, grouping=True)
        else:
            return '{:.6f}'.format(monto)

    @api.model
    def numero_a_letra(self,numero):
        return to_word(numero)

    
