import datetime

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import RedirectWarning


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    ruc_ci = fields.Char(string="RUC o CI")

    cuenta_liquidaciones = fields.Boolean(string="C. de Liquidaciones")
    cuenta_pago_proveedores = fields.Boolean(string="C. de Pago a Proveedores")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    facturas_pendientes_texto = fields.Html(string="Facturas Pendientes Texto")
    contacto_liquidaciones = fields.Boolean(string="Contacto de Liquidaciones", copy=False, default=False)

    cuenta_cobrar_ms_id = fields.Many2one('account.account', string="Cuenta a cobrar (Moneda extrajera)")
    cuenta_pagar_ms_id = fields.Many2one('account.account', string="Cuenta a pagar (Moneda extrajera)")

    @api.model
    def enviarCuentasCobrar(self):
        cuentas_cobrar = self.env['account.move'].search([
            ('company_id', '=', self.env.company.id),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ('not_paid', 'partial')),
            ('move_type', '=', 'out_invoice'),
            ('invoice_date_due','<=', datetime.date.today())
        ]).filtered(lambda inv: not any(inv.line_ids.mapped('blocked')))
        for p in set(cuentas_cobrar.mapped('commercial_partner_id')):
            facturas_pendientes = cuentas_cobrar.filtered(lambda x: x.commercial_partner_id == p)
            facturas_usd = facturas_pendientes.filtered(lambda x:x.currency_id.name == 'USD')
            facturas_pyg = facturas_pendientes.filtered(lambda x:x.currency_id.name == 'PYG')
            texto = '<table>' \
                    '<tr>' \
                    '<td style="border:1px solid black;padding:5px">Número</td>' \
                    '<td style="border:1px solid black;padding:5px">Fecha de Factura</td>' \
                    '<td style="border:1px solid black;padding:5px">Fecha de Vencimiento</td>' \
                    '<td style="border:1px solid black;padding:5px">Documento de Origen</td>' \
                    '<td style="border:1px solid black;padding:5px">Adeudo Total</td>' \
                    '</tr>'
            if facturas_usd:
                for f in facturas_usd:
                    texto += '<tr>' \
                                    '<td style="border:1px solid black;padding:5px">' + f.name + '</td>' \
                                                                                                 '<td style="border:1px ' \
                                                                                                 'solid black;padding:5px">' + \
                            f.invoice_date.strftime("%d/%m/%Y") + '</td><td style="border:1px solid black;padding:5px">' + \
                            f.invoice_date_due.strftime("%d/%m/%Y") + '</td>'
                    if f.invoice_origin:
                        texto += '<td style="border:1px solid black;padding:5px">' + f.invoice_origin + '</td>'
                    else:
                        texto += '<td style="border:1px solid black;padding:5px"/>'

                    texto += '<td style="border:1px solid black;padding:5px">' + f.currency_id.symbol + ' ' + \
                            str('{0:,.0f}'.format(f.amount_residual)).replace(",",
                                                                              ".") if f.amount_residual else '0' + '</td>' \
                                                                                                                   '</tr>'
                total_usd_seteado = 'USD ' + str('{0:,.0f}'.format(sum(facturas_usd.mapped('amount_residual')))).replace(",",".")
                texto += '<tr><td colspan="4"/><td style="padding:5px;font-weight:bold">' + total_usd_seteado + '</td></tr>'
                texto += '<tr rowspan="3"><td colspan="5"/></tr>'
            if facturas_pyg:
                for f in facturas_pyg:
                    texto += '<tr>' \
                                    '<td style="border:1px solid black;padding:5px">' + f.name + '</td>' \
                                                                                                 '<td style="border:1px ' \
                                                                                                 'solid black;padding:5px">' + \
                            f.invoice_date.strftime("%d/%m/%Y") + '</td><td style="border:1px solid black;padding:5px">' + \
                            f.invoice_date_due.strftime("%d/%m/%Y") + '</td>'
                    if f.invoice_origin:
                        texto += '<td style="border:1px solid black;padding:5px">' + f.invoice_origin + '</td>'
                    else:
                        texto += '<td style="border:1px solid black;padding:5px"/>'

                    texto += '<td style="border:1px solid black;padding:5px">' + f.currency_id.symbol + ' ' + \
                            str('{0:,.0f}'.format(f.amount_residual)).replace(",",
                                                                              ".") if f.amount_residual else '0' + '</td>' \
                                                                                                                   '</tr>'
                total_pyg_seteado = 'PYG ' + str('{0:,.0f}'.format(sum(facturas_pyg.mapped('amount_residual')))).replace(",",".")
                texto += '<tr><td colspan="4"/><td style="padding:5px;font-weight:bold">' + total_pyg_seteado + '</td></tr>'
            p.write({'facturas_pendientes_texto': texto})
            template = self.env.ref('bvpasa_account.mail_template_cuentas_cobrar')
            destinatarios = []
            destinatarios.append(p.id)
            copias = self.env.user.company_id.partner_id.email + ', '
            if p.child_ids:
                for c in p.child_ids.filtered(lambda x:x.email):
                    copias += c.email + ', '
            #destinatarios.append(self.env.company.id)
            vals = {
                'subject': 'Bolsa de Valores y Productos de Asunción S.A. Recordatorio de pago -  %s' % p.name,
                'auto_delete': False,
                'recipient_ids': destinatarios,
                'email_cc': copias,
                'email_from': self.env.user.company_id.email,
                'author_id': self.env.user.id,
            }
            template.send_mail(p.id, email_values=vals, force_send=True)
