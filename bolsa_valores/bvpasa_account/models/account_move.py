import datetime
from datetime import timedelta

from odoo import models, fields, api, exceptions,_
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang


class AccountMove(models.Model):
    _inherit = 'account.move'

    def computeLastPayment(self):
        for f in self:
            texto = False
            monto = 0
            monto_esperado = 0
            result = f.invoice_payment_term_id.compute(value=f.amount_total, currency=f.currency_id, date_ref= f.invoice_date)
            if result:
                texto = ''
                pagado = f.amount_total - f.amount_residual
                for l in result:
                    monto_esperado += float(l[1])
                    fecha = datetime.datetime.strptime(l[0], '%Y-%m-%d').date()
                    if fecha <= datetime.date.today():
                        if monto_esperado > pagado:
                            monto += float(l[1])
                            texto += '<tr>' \
                                     '<td style="border:1px solid black;padding:5px">' + f.name + '</td>' \
                                                                                                  '<td style="border:1px ' \
                                                                                                  'solid black;padding:5px">' + \
                                     f.invoice_date.strftime(
                                         "%d/%m/%Y") + '</td><td style="border:1px solid black;padding:5px">' + \
                                     fecha.strftime("%d/%m/%Y") + '</td>'
                            if f.invoice_origin:
                                texto += '<td style="border:1px solid black;padding:5px">' + f.invoice_origin + '</td>'
                            else:
                                texto += '<td style="border:1px solid black;padding:5px"/>'
                            texto += '<td style="border:1px solid black;padding:5px">' + f.currency_id.symbol + ' ' + \
                                     str('{0:,.0f}'.format(float(l[1]))).replace(",",
                                                                                    ".") if float(l[1]) else '0' + '</td>' \
                                                                                                                      '</tr>'
            if monto > 0:
                return texto, monto
            else:
                return False

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

    @api.model_create_multi
    def create(self, vals_list):
        adm_account = self.env['account.analytic.account'].search([('name','=','ADM')])
        if adm_account:
            for val in vals_list:
                if not 'analytic_account_id' in val or not val['analytic_account_id']:
                    val['analytic_account_id'] = adm_account.id
        return super().create(vals_list)

    def write(self, vals):
        if not self.analytic_account_id:
            if not 'analytic_account_id' in vals:
                adm_account = self.env['account.analytic.account'].search([('name', '=', 'ADM')])
                vals['analytic_account_id'] = adm_account.id
        res = super().write(vals)
        return res