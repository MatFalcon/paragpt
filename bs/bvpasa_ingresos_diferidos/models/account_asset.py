# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.tools import float_compare, float_is_zero, float_round
import time
from datetime import datetime, timedelta


class AccountAsset(models.Model):
    _inherit = 'account.asset'

    def days_between_dates(self, dt1, dt2):
        # Función que calcula la diferencia entre dos fechas dadas
        date_format = "%d/%m/%Y"
        a = time.mktime(time.strptime(dt1.strftime("%d/%m/%Y"), date_format))
        b = time.mktime(time.strptime(dt2.strftime("%d/%m/%Y"), date_format))
        delta = b - a
        return int(delta / 86400)

    @api.depends(
        'original_value', 'salvage_value', 'already_depreciated_amount_import',
        'depreciation_move_ids.state',
        'depreciation_move_ids.amount_total',
        'depreciation_move_ids.reversal_move_id'
    )
    def _compute_value_residual(self):
        """ Función que calcula el valor residual, teniendo en cuenta el valor original, el valor no depreciable,
        el valor ya depreciado y la suma del monto de las lineas ya depreciadas """
        for record in self:
            posted = record.depreciation_move_ids.filtered(
                lambda m: m.state == 'posted' and not m.reversal_move_id
            )
            record.value_residual = (
                    record.original_value
                    - record.salvage_value
                    - record.already_depreciated_amount_import
                    - sum(move.amount_total for move in posted)
            )

    def _compute_board_amount(self, computation_sequence, residual_amount, total_amount_to_depr, max_depreciation_nb,
                              starting_sequence, depreciation_date, costo_dia, date_anterior):
        amount = 0
        if computation_sequence == max_depreciation_nb:
            # la última linea siempre toma el monto residual
            amount = residual_amount
        else:
            if self.method in ('degressive', 'degressive_then_linear'):
                amount = residual_amount * self.method_progress_factor
            if self.method in ('linear', 'degressive_then_linear'):
                dif_days = self.days_between_dates(date_anterior, depreciation_date)
                linear_amount = costo_dia * dif_days
                if self.method == 'degressive_then_linear':
                    amount = max(linear_amount, amount)
                else:
                    amount = linear_amount
        return amount

    def _recompute_board(self, depreciation_number, starting_sequence, amount_to_depreciate, depreciation_date,
                         already_depreciated_amount, amount_change_ids):
        depreciation_number = depreciation_number - self.depreciation_number_import
        posted_depreciation_move_ids = self.depreciation_move_ids.filtered(
            lambda x: x.state == 'posted' and not x.asset_value_change and not x.reversal_move_id).sorted(
            key=lambda l: l.date)
        last_depreciation_date = False
        if posted_depreciation_move_ids:
            last_depreciation_date = fields.Date.from_string(posted_depreciation_move_ids[-1].date)
        self.ensure_one()
        residual_amount = amount_to_depreciate
        # Remove old unposted depreciation lines. We cannot use unlink() with One2many field
        move_vals = []
        if not last_depreciation_date:
            if not self.first_depreciation_date_import:
                primera_dif = self.days_between_dates(self.acquisition_date, self.first_depreciation_date)
            else:
                cant = self.depreciation_number_import - 1
                fecha_final = self.first_depreciation_date_import + timedelta(days=cant * 30)
                ultimo_dia_del_mes = calendar.monthrange(fecha_final.year, fecha_final.month)[1]
                fecha_final_con_ultimo_dia = datetime(fecha_final.year, fecha_final.month, ultimo_dia_del_mes)
                primera_dif = self.days_between_dates(fecha_final_con_ultimo_dia, self.first_depreciation_date)
        else:
            primera_dif = self.days_between_dates(last_depreciation_date, depreciation_date)
        dt1 = self.first_depreciation_date if not last_depreciation_date else depreciation_date
        if not self.prorata and self.prorata_date:
            dt2 = dt1 + relativedelta(months=self.method_number - 1, day=31)
        else:
            dt2 = self.prorata_date
        cant_dias = self.days_between_dates(dt1, dt2)
        costo_dia = amount_to_depreciate / (cant_dias + primera_dif)
        if last_depreciation_date:
            date_anterior = last_depreciation_date
        elif self.first_depreciation_date_import:
            cant = self.depreciation_number_import - 1
            fecha_final = self.first_depreciation_date_import + timedelta(days=cant * 30)
            ultimo_dia_del_mes = calendar.monthrange(fecha_final.year, fecha_final.month)[1]
            date_anterior = datetime(fecha_final.year, fecha_final.month, ultimo_dia_del_mes)
        else:
            date_anterior = self.acquisition_date
        if self.prorata:
            depreciation_number = depreciation_number - 1
        if amount_to_depreciate != 0.0:
            for asset_sequence in range(starting_sequence + 1, depreciation_number + 1):
                while amount_change_ids and amount_change_ids[0].date <= depreciation_date:
                    if not amount_change_ids[0].reversal_move_id:
                        residual_amount -= amount_change_ids[0].amount_total
                        amount_to_depreciate -= amount_change_ids[0].amount_total
                        already_depreciated_amount += amount_change_ids[0].amount_total
                    amount_change_ids[0].write({
                        'asset_remaining_value': float_round(residual_amount,
                                                             precision_rounding=self.currency_id.rounding),
                        'asset_depreciated_value': amount_to_depreciate - residual_amount + already_depreciated_amount,
                    })
                    amount_change_ids -= amount_change_ids[0]
                amount = self._compute_board_amount(asset_sequence, residual_amount, amount_to_depreciate,
                                                    depreciation_number, starting_sequence, depreciation_date,
                                                    costo_dia, date_anterior)
                prorata_factor = 1
                move_ref = self.name + ' (%s/%s)' % (asset_sequence, self.method_number)
                amount = self.currency_id.round(amount * prorata_factor)
                if float_is_zero(amount, precision_rounding=self.currency_id.rounding):
                    continue
                residual_amount -= amount

                move_vals.append(self.env['account.move']._prepare_move_for_asset_depreciation({
                    'amount': amount,
                    'asset_id': self,
                    'move_ref': move_ref,
                    'date': depreciation_date,
                    'asset_remaining_value': float_round(residual_amount, precision_rounding=self.currency_id.rounding),
                    'asset_depreciated_value': amount_to_depreciate - residual_amount + already_depreciated_amount,
                }))
                date_anterior = depreciation_date
                depreciation_date = depreciation_date + relativedelta(months=+int(self.method_period))
                # datetime doesn't take into account that the number of days is not the same for each month
                if int(self.method_period) % 12 != 0:
                    max_day_in_month = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=max_day_in_month)
                if asset_sequence == depreciation_number - 1 and self.prorata_date and self.prorata:
                    depreciation_date = self.prorata_date
        return move_vals
