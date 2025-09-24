from odoo import models, fields, api, exceptions


class AccountMove(models.Model):
    _inherit = 'account.move'

    purchase_message = fields.Boolean(string="Mensaje", default=False)

    retencion_generada = fields.Boolean(string="Retención generada", default=False,copy=False, tracking=True)


    @api.model
    def getDataEmailRetencion(self):
        registros = self.env['account.move'].search([('partner_id.property_account_position_id.retencion_extranjeros','=',True),
                                                     ('move_type','=','in_invoice'),
                                                     ('state','=','posted'),
                                                     ('retencion_generada','=',False)])
        texto = ""
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



    @api.onchange('invoice_line_ids', 'partner_id')
    def onchangeInvoiceLinePartner(self):
        for s in self:
            if s.move_type == "in_invoice":
                productos = s.mapped('invoice_line_ids.product_id.id')
                if productos:
                    purchase_lines = self.env['purchase.order.line'].search([('partner_id', '=', s.partner_id.id),
                                                                             ('qty_invoiced', '<', 0.1),
                                                                             ('product_id', 'in', productos),
                                                                             ('order_id.state', '=', 'purchase')])
                    if purchase_lines:
                        s.update({'purchase_message': True})
                    else:
                        s.update({'purchase_message': False})
                else:
                    s.update({'purchase_message': False})

    def action_post(self):
        for s in self:
            if s.move_type == "in_invoice" and s.purchase_message:
                raise exceptions.ValidationError('No se puede confirmar la factura. El proveedor cuenta con una orden '
                                                 'de compra por el mismo ítem a facturar.')
        return super(AccountMove, self).action_post()
