import datetime
import logging
from odoo import models, fields, api, exceptions, _
from odoo.exceptions import RedirectWarning

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    facturas_pendientes_texto = fields.Html(string="Facturas Pendientes Texto")

    @api.model
    def enviarRecordatorioEmisores(self):
        etiqueta_emisor = self.env['res.partner.category'].search([
            ('name', '=', 'Emisores')
        ])
        _logger.info(f"Etiqueta encontrada: {etiqueta_emisor}")
        etiqueta_emisor_id = etiqueta_emisor.id
        if etiqueta_emisor:
            contactos_emisores = self.env['res.partner'].search([
                ('category_id', '=', etiqueta_emisor_id)
            ])
            # contactos_emisores = self.env['res.partner'].search([
            #     ('email', '=', 'emmanuel.falcon@sati.com.py')
            # ])
            _logger.info(f"Contactos: {len(contactos_emisores)}")
            for contacto in contactos_emisores:
                vals = {
                    'subject': 'Solicitud de Estados Financieros',
                    'auto_delete': False,
                    'recipient_ids': [contacto.id],
                    'email_cc': 'administracion@bolsadevalores.com.py',
                    'email_from': self.env.user.company_id.email,
                    'author_id': self.env.user.id,
                }
                template = self.env.ref('bva_custom.mail_template_recordatorio_emisores')

                template.send_mail(contacto.id, email_values=vals, force_send=True)
                _logger.info(f"Se envio el correo{etiqueta_emisor}")


    @api.model
    def enviarCuentasCobrar(self):
        # cuentas_cobrar = self.env['account.move'].search([
        #     ('company_id', '=', self.env.company.id),
        #     ('state', '=', 'posted'),
        #     ('payment_state', 'in', ('not_paid', 'partial')),
        #     ('move_type', '=', 'out_invoice'),
        #     # ('no_reclamar_cobro','=',False),
        #     ('invoice_date_due', '<=', datetime.date.today())
        # ]).filtered(lambda inv: not any(inv.line_ids.mapped('blocked')))
        lineas_vencidas = self.env['account.move.line'].search([
            ('company_id', '=', self.env.company.id),
            ('parent_state', '=', 'posted'),
            ('move_id.payment_state', 'in', ('not_paid', 'partial')),
            ('move_id.move_type', '=', 'out_invoice'),
            ('date_maturity', '<=', datetime.date.today())
        ])

        # _logger.warning("lineas moves %s %s", len(lineas_vencidas.mapped('move_id')), lineas_vencidas.mapped('move_id'))

        cuentas_cobrar = lineas_vencidas.mapped('move_id').filtered(lambda inv: not any(inv.line_ids.mapped('blocked')))
        _logger.warning('len cuentas cobrarr %s', len(cuentas_cobrar))

        # _logger.warning("lineas vencidas %s %s", len(lineas_vencidas), lineas_vencidas)
        # lineas_cobrar = self.env['account.move.line'].search([('move_id', 'in', cuentas_cobrar.ids),('date_maturity','!=',False)])
        # _logger.warning("cuentas lineas cobrar %s", lineas_cobrar)

        cuentas_cobrar = cuentas_cobrar.filtered(lambda x: not x.invoice_payment_term_id
                                                           or len(x.invoice_payment_term_id.line_ids) == 1
                                                           or x.computeLastPayment())
        for p in set(cuentas_cobrar.mapped('commercial_partner_id')):
            facturas_pendientes = cuentas_cobrar.filtered(lambda x: x.commercial_partner_id == p)
            facturas_usd = facturas_pendientes.filtered(lambda x: x.currency_id.symbol == 'USD') # name_tesaka o symbol
            facturas_pyg = facturas_pendientes.filtered(lambda x: x.currency_id.symbol == 'PYG') # name_tesaka o symbol
            suma_facturas_usd = 0
            suma_facturas_pyg = 0
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
                    print(f.computeLastPayment())
                    texto_cuota, monto = f.computeLastPayment()
                    monto = 0
                    for line in f.line_ids.filtered(lambda l: l.date_maturity and l.date_maturity <= datetime.date.today()):
                        monto += line.amount_residual_currency
                    _logger.warning('monto a correo %s', monto)
                    if not texto_cuota:
                        suma_facturas_usd += f.amount_residual
                        texto += '<tr>' \
                                 '<td style="border:1px solid black;padding:5px">' + f.name + '</td>' \
                                                                                              '<td style="border:1px ' \
                                                                                              'solid black;padding:5px">' + \
                                 f.invoice_date.strftime(
                                     "%d/%m/%Y") + '</td><td style="border:1px solid black;padding:5px">' + \
                                 f.invoice_date_due.strftime("%d/%m/%Y") + '</td>'
                        if f.invoice_origin:
                            texto += '<td style="border:1px solid black;padding:5px">' + f.invoice_origin + '</td>'
                        else:
                            texto += '<td style="border:1px solid black;padding:5px"/>'

                        texto += '<td style="border:1px solid black;padding:5px">' + f.currency_id.symbol + ' ' + \
                                 str('{0:,.2f}'.format(f.amount_residual)).replace(",",
                                                                                   ".") if f.amount_residual else '0' + '</td>' \
                                                                                                                        '</tr>'
                    else:
                        texto += texto_cuota
                        suma_facturas_usd += monto
                total_usd_seteado = 'USD ' + str(
                    '{0:,.2f}'.format(suma_facturas_usd)).replace(",", ".")
                texto += '<tr><td colspan="4"/><td style="padding:5px;font-weight:bold">' + total_usd_seteado + '</td></tr>'
                texto += '<tr rowspan="3"><td colspan="5"/></tr>'
            if facturas_pyg:
                for f in facturas_pyg:
                    texto_cuota, monto = f.computeLastPayment()
                    monto = 0
                    for line in f.line_ids.filtered(lambda l: l.date_maturity and l.date_maturity <= datetime.date.today()):
                        monto += line.amount_residual
                    _logger.warning('monto a correo %s', monto)
                    if not texto_cuota:
                        suma_facturas_pyg += f.amount_residual
                        texto += '<tr>' \
                                 '<td style="border:1px solid black;padding:5px">' + f.name + '</td>' \
                                                                                              '<td style="border:1px ' \
                                                                                              'solid black;padding:5px">' + \
                                 f.invoice_date.strftime(
                                     "%d/%m/%Y") + '</td><td style="border:1px solid black;padding:5px">' + \
                                 f.invoice_date_due.strftime("%d/%m/%Y") + '</td>'
                        if f.invoice_origin:
                            texto += '<td style="border:1px solid black;padding:5px">' + f.invoice_origin + '</td>'
                        else:
                            texto += '<td style="border:1px solid black;padding:5px"/>'

                        texto += '<td style="border:1px solid black;padding:5px">' + f.currency_id.symbol + ' ' + \
                                 str('{0:,.0f}'.format(f.amount_residual)).replace(",",
                                                                                   ".") if f.amount_residual else '0' + '</td>' \
                                                                                                                        '</tr>'
                    else:
                        texto += texto_cuota
                        # suma_facturas_pyg += f.amount_residual
                        suma_facturas_pyg += monto
                total_pyg_seteado = 'PYG ' + str(
                    '{0:,.0f}'.format(suma_facturas_pyg)).replace(",", ".")
                texto += '<tr><td colspan="4"/><td style="padding:5px;font-weight:bold">' + total_pyg_seteado + '</td></tr>'
            p.write({'facturas_pendientes_texto': texto})
            template = self.env.ref('bvpasa_account.mail_template_cuentas_cobrar')
            destinatarios = []
            destinatarios.append(p.id)
            copias = self.env.user.company_id.partner_id.email + ', '
            if p.child_ids:
                for c in p.child_ids.filtered(lambda x: x.email):
                    copias += c.email + ', '
            # destinatarios.append(self.env.company.id)
            vals = {
                'subject': 'Bolsa de Valores y Productos de Asunción S.A. Recordatorio de pago -  %s' % p.name,
                'auto_delete': False,
                'recipient_ids': destinatarios,
                'email_cc': copias,
                'email_from': self.env.user.company_id.email,
                'author_id': self.env.user.id,
            }
            template.send_mail(p.id, email_values=vals, force_send=True)