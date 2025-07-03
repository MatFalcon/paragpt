import datetime
from datetime import timedelta

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import RedirectWarning, UserError, ValidationError, AccessError
from odoo.tools.misc import formatLang, format_date, get_lang
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    no_reclamar_cobro = fields.Boolean(string='No reclamar cobro')
    format_monto = fields.Char(string="Monto Formateado")
    notificar_retencion = fields.Boolean(string="Notificar Retencion")
    

    @api.model
    def getDataEmailRetencion(self):
        registros = self.env['account.move'].search([('move_type','=','in_invoice'),
                                                     ('state','=','posted'),
                                                     ('notificar_retencion','=',True)])
        texto = ""
        print("Registros", registros)
        if registros:
            partners = set(registros.mapped('partner_id'))
            company_id = set(registros.mapped('company_id'))
            for p in partners:
                texto = texto + '<b>' + p.name + '</b><br/>'
                texto = texto + '<table><tr><td style="border:1px solid black;padding:5px">Número</td><td ' \
                                'style="border:1px solid black;padding:5px">Fecha de factura</td><td style="border:1px '\
                                'solid black;padding:5px">Fecha de Vencimiento</td><td style="border:1px solid ' \
                                'black;padding:5px">Monto</td><td style="border:1px solid ' \
                                'black;padding:5px">Moneda</td></tr>'
                for r in registros.filtered(lambda x: x.partner_id == p):
                    texto = texto + '<tr><td style="border:1px solid black;padding:5px">' + r.name +\
                            '</td><td style="border:1px solid black;padding:5px">'+ r.invoice_date.strftime("%d/%m/%Y") +\
                            '</td><td style="border:1px solid black;padding:5px">'+r.invoice_date_due.strftime("%d/%m/%Y")+\
                            '</td><td style="border:1px solid black;padding:5px">'+ str('{0:,.0f}'.format(r.amount_total_signed)).replace(",",".")+\
                            '</td><td style="border:1px solid black;padding:5px">'+r.currency_id.name + \
                            '</td></tr>'
                texto = texto + '</table>'
            destinatarios = []
            for c in company_id:
                destinatarios.append(c.partner_id.id)
            vals = {
                'subject': 'Retenciones pendientes por Facturas del Exterior',
                'body_html': texto,
                'recipient_ids':destinatarios,
                'auto_delete': False,
                'email_from': 'administracion@bolsadevalores.com.py',
                'author_id': self.user_id.id,
            }
            mail_id = self.env['mail.mail'].sudo().create(vals)
            mail_id.sudo().send()



    def calculate_payment_terms(self, invoice):
        payment_term = invoice.invoice_payment_term_id
        amount_total = invoice.amount_total
        currency = invoice.currency_id
        invoice_date = invoice.invoice_date

        # Obtener los montos de impuestos de la factura
        tax_amount = invoice.amount_tax
        tax_lines = invoice.line_ids.filtered(lambda line: line.tax_ids)
        total_tax_amount_currency = sum(tax_line.amount_currency for tax_line in tax_lines)

        # Obtener la cantidad neta (sin impuestos)
        untaxed_amount = invoice.amount_untaxed
        untaxed_amount_currency = invoice.amount_total_in_currency_signed

        if not payment_term:
            return []

        # Obtener los términos de pago usando el método _compute_terms
        terms = payment_term._compute_terms(
            date_ref=invoice_date,
            currency=currency,
            company=invoice.company_id,
            tax_amount=tax_amount,
            tax_amount_currency=total_tax_amount_currency,
            untaxed_amount=untaxed_amount,
            untaxed_amount_currency=untaxed_amount_currency,
            sign=1
        )
        _logger.warning("terms %s", terms)

        # Extraer la información necesaria de los términos calculados
        payment_dates = []
        for term in terms['line_ids']:
            date = term['date']
            amount = term['company_amount']
            payment_dates.append((date.strftime('%Y-%m-%d'), amount))

        _logger.warning("payment dates %s", payment_dates)

        return payment_dates

    # def computeLastPayment(self):
    #     for invoice in self:
    #         if invoice.currency_id.symbol == 'USD':
    #             formatear_moneda = str('{0:,.2f}'.format(float(invoice.amount_residual)))
    #         if invoice.currency_id.symbol == 'PYG':
    #             formatear_moneda = str('{0:,.0f}'.format(float(invoice.amount_residual)))
    #         texto = False
    #         monto = 0
    #         monto_esperado = 0

    #         result = self.calculate_payment_terms(invoice)
    #         if result:
    #             texto = ''
    #             pagado = invoice.amount_total - invoice.amount_residual
    #             for l in result:
    #                 fecha = datetime.datetime.strptime(l[0], '%Y-%m-%d').date()
    #                 if fecha <= datetime.date.today():
    #                     monto += float(l[1])
    #                     texto += '<tr>' \
    #                              '<td style="border:1px solid black;padding:5px">' + invoice.name + '</td>' \
    #                                                                                                 '<td style="border:1px solid black;padding:5px">' + \
    #                              invoice.invoice_date.strftime(
    #                                  "%d/%m/%Y") + '</td><td style="border:1px solid black;padding:5px">' + \
    #                              fecha.strftime("%d/%m/%Y") + '</td>'
    #                     if invoice.invoice_origin:
    #                         texto += '<td style="border:1px solid black;padding:5px">' + invoice.invoice_origin + '</td>'
    #                     else:
    #                         texto += '<td style="border:1px solid black;padding:5px"/>'
    #                     texto += '<td style="border:1px solid black;padding:5px">' + invoice.currency_id.symbol + ' ' + \
    #                              formatear_moneda.replace(",", ".") if invoice.amount_residual else '0' + '</td>' \
    #                                                                                                              '</tr>'
    #         if monto > 0:
    #             return texto, monto
    #         else:
    #             return False
    def computeLastPayment(self):
        for invoice in self:
            for line in invoice.line_ids.filtered(lambda l: l.date_maturity and l.date_maturity <= datetime.date.today()):
                residual = 0
                if line.currency_id != line.company_currency_id:
                    residual += line.amount_residual_currency
                else:
                    residual += line.amount_residual

            # Formatear la moneda según el símbolo
            if invoice.currency_id.symbol == 'USD':
                formatear_moneda = '{:,.2f}'.format(residual)
            elif invoice.currency_id.symbol == 'PYG':
                formatear_moneda = '{:,.0f}'.format(residual)
            else:
                formatear_moneda = '{:,.2f}'.format(residual)
    
            texto = False
            monto = 0
    
            # Obtener los términos de pago
            result = self.calculate_payment_terms(invoice)
            if result:
                texto = ''
                pagado = invoice.amount_total - invoice.amount_residual
                for l in result:
                    fecha = datetime.datetime.strptime(l[0], '%Y-%m-%d').date()
                    if fecha <= datetime.date.today():
                        monto += l[1]  # `l[1]` ya es un flotante
                        texto += '<tr>' \
                                 '<td style="border:1px solid black;padding:5px">' + invoice.name + '</td>' \
                                 '<td style="border:1px solid black;padding:5px">' + \
                                 invoice.invoice_date.strftime("%d/%m/%Y") + '</td>' \
                                 '<td style="border:1px solid black;padding:5px">' + \
                                 fecha.strftime("%d/%m/%Y") + '</td>'
                        if invoice.invoice_origin:
                            texto += '<td style="border:1px solid black;padding:5px">' + invoice.invoice_origin + '</td>'
                        else:
                            texto += '<td style="border:1px solid black;padding:5px"/>'
                        texto += '<td style="border:1px solid black;padding:5px">' + invoice.currency_id.symbol + ' ' + \
                                 formatear_moneda.replace(",", ".") if invoice.amount_residual else '0' + '</td>' \
                                                                                                             '</tr>'
            if monto > 0:
                return texto, monto
                _logger.warning('return monto y texto')
            else:
                _logger.warning('return false')
                return False

