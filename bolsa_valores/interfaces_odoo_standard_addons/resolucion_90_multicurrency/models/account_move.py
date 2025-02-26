# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def get_monto10(self, currency_id=False):
        # resolucion_90_multicurrency/models/resolucion_90_wizard.py
        result = super(AccountMove, self).get_monto10()
        if currency_id and currency_id != self.company_id.currency_id:
            result = int(self.company_id.currency_id._convert(result, currency_id, self.env.company, self.date))
        return result

    def get_monto5(self, currency_id=False):
        # resolucion_90_multicurrency/models/resolucion_90_wizard.py
        result = super(AccountMove, self).get_monto5()
        if currency_id and currency_id != self.company_id.currency_id:
            result = int(self.company_id.currency_id._convert(result, currency_id, self.env.company, self.date))
        return result

    def get_monto_exento(self, currency_id=False):
        # resolucion_90_multicurrency/models/resolucion_90_wizard.py
        result = super(AccountMove, self).get_monto_exento()
        if currency_id and currency_id != self.company_id.currency_id:
            result = int(self.company_id.currency_id._convert(result, currency_id, self.env.company, self.date))
        return result

    def get_monto_total(self, currency_id=False):
        # resolucion_90_multicurrency/models/resolucion_90_wizard.py
        result = super(AccountMove, self).get_monto_total()
        if currency_id and currency_id != self.company_id.currency_id:
            result = int(self.company_id.currency_id._convert(result, currency_id, self.env.company, self.date))
        return result
