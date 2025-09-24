from odoo import api, models, fields


class AccountMoveCustom(models.Model):
    _inherit = 'account.move'

    def _post(self, soft=True):
        to_post = super()._post(soft)
        move_ids = [move.id for move in to_post]
        novedades = self.env['pbp.novedades'].search([('invoice_id', 'in', move_ids)])
        novedades.write({'state': 'publicado'})
        return to_post

    def _compute_amount(self):
        for move in self:
            if not move.line_ids:
                continue

            total = 0
            for line in move.line_ids:
                if not line.from_novedades:
                    return super()._compute_amount()
                total += line.price_total

            move.amount_total = total
            move.amount_total_signed = total
            move.amount_total_in_currency_signed = total


class AccountMoveLineCustom(models.Model):
    _inherit = 'account.move.line'

    price_subtotal_raw = fields.Float()
    from_novedades = fields.Boolean()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        for line in lines:
            if not line.from_novedades:
                continue
            line.price_subtotal = line.price_subtotal_raw
            line.price_total = line.price_subtotal_raw
        return lines
