import datetime

from odoo import models, fields, api, exceptions,_
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
    _inherit = 'account.move'

    def button_anular(self):
        res = super(AccountMove, self).button_anular()
        for i in self:
            if i.move_type == 'out_invoice':
                i.enviarFacturaAnulada()
        return res

    def enviarFacturaAnulada(self):
        template = self.env.ref('bvpasa_account.mail_template_factura_anulada')
        destinatarios = self.mapped('partner_id.child_ids.id')
        destinatarios.append(self.partner_id.id)
        destinatarios.append(self.env.user.company_id.partner_id.id)
        if destinatarios:
            vals = {
                'recipient_ids': destinatarios,
                'email_from': self.env.user.company_id.email,
                'author_id': self.env.user.id
            }
            template.send_mail(self.id, email_values=vals, force_send=True)


    def action_post(self):
        res = super(AccountMove, self).action_post()
        for i in self:
            if i.move_type in ['out_invoice', 'out_refund']:
                i.message_subscribe([p.id for p in [i.company_id.partner_id] if p not in i.sudo().message_partner_ids])
        return res

    def _check_fiscalyear_lock_date(self):
        for move in self:
            lock_date = move.company_id._get_user_fiscal_lock_date()
            if move.date <= lock_date or (move.invoice_date and move.invoice_date <= lock_date):
                if self.user_has_groups('account.group_account_manager'):
                    message = _("No puede agregar/modificar asientos anteriores y hasta la fecha de bloqueo %s.", format_date(self.env, lock_date))
                else:
                    message = _('No puede agregar/modificar asientos anteriores y hasta la fecha de bloqueo %s. '
                                'Compruebe la configuración de la empresa o consulte a alguien con la función de \"asesor\"', format_date(self.env, lock_date))
                raise UserError(message)
        return True

    @api.onchange('currency_id', 'invoice_date', 'date')
    def getCurrrencyRateDate(self):
        for i in self:
            if i.currency_id.name == "USD" and i.invoice_date:
                rate_today = i.env['res.currency.rate'].search([('name','=', datetime.date.today()),
                                                                ('currency_id','=',self.currency_id.id)])
                if not rate_today:
                    raise exceptions.ValidationError('No existe una tasa de cambio a la fecha de la factura. Favor '
                                                     'verificar')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.onchange('product_id')
    def _product_id_onchange(self):
        for s in self:
            if s.move_id.currency_id.name == 'USD' and s.move_id.move_type == "out_invoice":
                s.price_unit = s.product_id.list_price_ext
