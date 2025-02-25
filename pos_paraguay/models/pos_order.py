# -*- coding: utf-8 -*-
import psycopg2
import logging

from odoo import api, fields, models, tools,_
from odoo.exceptions import ValidationError,UserError
_logger = logging.getLogger(__name__)


class AccountMoveLineInhe(models.Model):
    _inherit = "account.move.line"

    tax_name = fields.Char("Nombre Impuesto", compute="_compute_tax_name", store=True)
    # traer campos cod barra y nombre del product para no agregar logica de javascript
    nombre_ticket = fields.Char(compute="_compute_tax_name")
    cod_barra = fields.Char(compute="_compute_tax_name")
    talla = fields.Char(compute="_compute_tax_name")

    @api.depends("product_id", "product_id.taxes_id", "talla")
    def _compute_tax_name(self):
        for record in self:
            if record.product_id:
                nombre_imp = None
                for t in record.tax_ids:
                    nombre_imp = str(t.name).replace("IVA", "").lstrip().rstrip()
                if record.product_id.product_tmpl_id.product_size_id:
                    record.talla = record.product_id.product_tmpl_id.product_size_id.name
                record.tax_name = nombre_imp
                template = record.product_id.product_tmpl_id
                if template:
                    nombre_product = template.name
                    if len(nombre_product) > 17:
                        nombre_product = nombre_product[0:14] + "..."
                    else:
                        nombre_product = template.name
                    record.nombre_ticket = nombre_product
                    record.cod_barra = template.barcode
            else:
                record.tax_name = False
                record.nombre_ticket = False
                record.cod_barra = False
                record.talla = False

class PosOrderParaguay(models.Model):
    _inherit = "pos.order"

    es_facturador_electronico = fields.Boolean(compute="get_test_env")
    nombre_marca = fields.Char(compute="_get_marca")
    tel_personalizado = fields.Char(compute="_compute_tel_personalizado")
    descripcion_compania = fields.Char(compute="_compute_tel_personalizado")
    @api.depends("tel_personalizado", "descripcion_compania")
    def _compute_tel_personalizado(self):
        for record in self:
            record.tel_personalizado = record.session_id.config_id.tel_punto_venta
            record.descripcion_compania = record.session_id.config_id.descripcion_compania
    def action_view_invoice(self):
        for rec in self:
            if rec.amount_total<0:
                return {
                    'name': _('Nota de Credito'),
                    'view_mode': 'form',
                    'view_id': self.env.ref('account.view_move_form').id,
                    'res_model': 'account.move',
                    'context': "{'move_type':'out_refund'}",
                    'type': 'ir.actions.act_window',
                    'res_id': self.account_move.id,
                }
            else:
                res=super(PosOrderParaguay,self).action_view_invoice()
                return res

    @api.depends('company_id')
    def get_test_env(self):
        for rec in self:
            if rec.company_id:

                rec.es_facturador_electronico = True if rec.company_id.servidor else False
            else:

                rec.es_facturador_electronico = False

    @api.depends("session_id")
    def _get_marca(self):
        for rec in self:
            rec.nombre_marca = rec.session_id.config_id.name
    # nro_factura=fields.Char(string='Nro Factura')
    # timbrado=fields.Char(string='Timbrado')
    #
    # def _order_fields(self, ui_order):
    #     rec = super(PosOrderParaguay,self)._order_fields(ui_order)
    #     # 'pos_reference': ui_order['name'],
    #     _logger.info('timbradillo')
    #     _logger.info( ui_order.get('timbrados', False))
    #     rec['timbrado']= ui_order.get('timbrados', False)
    #     return rec


    def _generate_pos_order_invoice(self):
        vals=super(PosOrderParaguay,self.with_context(generate_pdf=False))._generate_pos_order_invoice()

        # self.ensure_one()
    def _prepare_invoice_vals(self):
        vals=super(PosOrderParaguay,self)._prepare_invoice_vals()
        self.ensure_one()


        if self.amount_total < 0:
            talonario = self.config_id.talonario_nota_credito
            vals['timbrado'] = str(self.config_id.talonario_nota_credito.name)
            tipo_comprobante = self.env.ref('paraguay_backoffice.tipo_comprobante_3').id

        else:
            talonario =  self.config_id.talonario_factura
            vals['timbrado'] = str(self.config_id.talonario_factura.name)
            tipo_comprobante = self.env.ref('paraguay_backoffice.tipo_comprobante_1').id
        vals['talonario_factura'] = talonario.id
        vals['suc'] = talonario.suc
        vals['sec'] = talonario.sec
        nro=str(talonario.get_nro_and_ser_next()).zfill(7)
        vals['nro'] = nro
        vals['nro_factura'] = str(talonario.suc) + '-' + str(talonario.sec) + '-' + str(nro)
        vals['tipo_factura'] = '1'
        vals['tipo_comprobante'] = tipo_comprobante
        # self.account_move.sudo().remision()
        # self.account_move.name = self.account_move.nro_factura
        # vals['ref'] =
        # vals = {
        #     'invoice_origin': self.name,
        #     'pos_refunded_invoice_ids': pos_refunded_invoice_ids,
        #     'journal_id': self.session_id.config_id.invoice_journal_id.id,
        #     'move_type': 'out_invoice' if self.amount_total >= 0 else 'out_refund',
        #     'ref': self.name,
        #     'partner_id': self.partner_id.id,
        #     'partner_bank_id': self._get_partner_bank_id(),
        #     'currency_id': self.currency_id.id,
        #     'invoice_user_id': self.user_id.id,
        #     'invoice_date': invoice_date.astimezone(timezone).date(),
        #     'fiscal_position_id': self.fiscal_position_id.id,
        #     'invoice_line_ids': self._prepare_invoice_lines(),
        #     'invoice_payment_term_id': self.partner_id.property_payment_term_id.id or False,
        #     'invoice_cash_rounding_id': self.config_id.rounding_method.id
        #     if self.config_id.cash_rounding and (not self.config_id.only_round_cash_method or any(p.payment_method_id.is_cash_count for p in self.payment_ids))
        #     else False
        # }
        # if self.refunded_order_ids.account_move:
        #     vals['ref'] = _('Reversal of: %s', self.refunded_order_ids.account_move.name)
        #     vals['reversed_entry_id'] = self.refunded_order_ids.account_move.id
        # if self.note:
        #     vals.update({'narration': self.note})
        return vals

    # @api.model
    # def create_from_uis(self, orders, draft=False):
    #     """ Create and update Orders from the frontend PoS application.
    #
    #     Create new orders and update orders that are in draft status. If an order already exists with a status
    #     diferent from 'draft'it will be discareded, otherwise it will be saved to the database. If saved with
    #     'draft' status the order can be overwritten later by this function.
    #
    #     :param orders: dictionary with the orders to be created.
    #     :type orders: dict.
    #     :param draft: Indicate if the orders are ment to be finalised or temporarily saved.
    #     :type draft: bool.
    #     :Returns: list -- list of db-ids for the created and updated orders.
    #     """
    #     order_ids = []
    #     for order in orders:
    #         existing_order = False
    #         if 'server_id' in order['data']:
    #             existing_order = self.env['pos.order'].search(
    #                 ['|', ('id', '=', order['data']['server_id']), ('pos_reference', '=', order['data']['name'])],
    #                 limit=1)
    #         if (existing_order and existing_order.state == 'draft') or not existing_order:
    #             order_ids.append(self._process_order(order, draft, existing_order))
    #         orden=self.env['pos.order'].browse(order_ids)
    #         for ord in orden:
    #
    #             if ord.picking_ids:
    #                 picking_sin_partner=ord.picking_ids.filtered(lambda r: not r.partner_id)
    #                 for pick in picking_sin_partner:
    #                     pick.partner_id=ord.partner_id
    #             if ord.account_move:
    #                 sale_order = ord.lines.mapped('sale_order_origin_id')
    #                 if sale_order:
    #                     commercial = sale_order[0].user_id
    #                     ord.account_move.invoice_user_id = commercial
    #                 #Se pone si es NOta de Credito
    #                 if ord.amount_total <0:
    #                     ord.account_move.talonario_factura = ord.config_id.talonario_nota_credito
    #                     ord.account_move.timbrado = str(ord.config_id.talonario_nota_credito.name)
    #                     tipo_comprobante = self.env.ref('paraguay_backoffice.tipo_comprobante_3')
    #
    #                 else:
    #                     ord.account_move.talonario_factura = ord.config_id.talonario_factura
    #                     ord.account_move.timbrado = str(ord.config_id.talonario_factura.name)
    #                     tipo_comprobante = self.env.ref('paraguay_backoffice.tipo_comprobante_1')
    #                 ord.account_move.tipo_factura = '1'
    #                 ord.account_move.tipo_comprobante = tipo_comprobante
    #                 ord.account_move.sudo().remision()
    #                 ord.account_move.name=ord.account_move.nro_factura
    #                 # ord.account_move.sudo().action_post()
    #     return self.env['pos.order'].search_read(domain=[('id', 'in', order_ids)], fields=['id', 'pos_reference'])

    # @api.model
    # def create_from_ui(self, orders):
    #     # Keep only new orders
    #     submitted_references = [o['data']['name'] for o in orders]
    #     pos_order = self.search([('pos_reference', 'in', submitted_references)])
    #     existing_orders = pos_order.read(['pos_reference'])
    #     existing_references = set([o['pos_reference'] for o in existing_orders])
    #     orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
    #     order_ids = []
    #
    #     for tmp_order in orders_to_save:
    #         to_invoice = tmp_order['to_invoice']
    #         order = tmp_order['data']
    #         if to_invoice:
    #             self._match_payment_to_invoice(order)
    #         pos_order = self._process_order(order)
    #         order_ids.append(pos_order.id)
    #
    #         try:
    #             pos_order.action_pos_order_paid()
    #         except psycopg2.OperationalError:
    #             # do not hide transactional errors, the order(s) won't be saved!
    #             raise
    #         except Exception as e:
    #             _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))
    #
    #         if to_invoice:
    #             pos_order.action_pos_order_invoice()
    #             pos_order.invoice_id.talonario_factura = self.env.user.documento_factura
    #             pos_order.invoice_id.timbrado = str(self.invoice_id.talonario_factura.name)
    #             tipo_comprobante = self.env.ref('paraguay_backoffice.tipo_comprobante_1')
    #             pos_order.invoice_id.tipo_factura = 1
    #             pos_order.invoice_id.tipo_comprobante = tipo_comprobante
    #             pos_order.invoice_id.sudo().remision()
    #             pos_order.invoice_id.sudo().action_invoice_open()
    #             # raise ValidationError('pos nuestro')
    #             pos_order.account_move = pos_order.invoice_id.move_id
    #     return order_ids

    # @api.multi
    # def action_pos_order_invoice(self):
    #     Invoice = self.env['account.invoice']
    #
    #
    #     for order in self:
    #         # Force company for all SUPERUSER_ID action
    #         local_context = dict(self.env.context, force_company=order.company_id.id, company_id=order.company_id.id)
    #         if order.invoice_id:
    #             Invoice += order.invoice_id
    #             continue
    #
    #         if not order.partner_id:
    #             raise UserError(_('Please provide a partner for the sale.'))
    #
    #         invoice = Invoice.new(order._prepare_invoice())
    #         invoice._onchange_partner_id()
    #         invoice.fiscal_position_id = order.fiscal_position_id
    #
    #         inv = invoice._convert_to_write({name: invoice[name] for name in invoice._cache})
    #         new_invoice = Invoice.with_context(local_context).sudo().create(inv)
    #         # print('new_invoice',new_invoice)
    #         message = _("This invoice has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
    #         new_invoice.message_post(body=message)
    #         # print(new_invoice.set_numero_factura)
    #         # print('new invoice -> 2 ',new_invoice.nro_factura)
    #         order.write({'invoice_id': new_invoice.id, 'state': 'invoiced'})
    #         Invoice += new_invoice
    #
    #         for line in order.lines:
    #             self.with_context(local_context)._action_create_invoice_line(line, new_invoice.id)
    #
    #         new_invoice.with_context(local_context).sudo().compute_taxes()
    #         order.sudo().write({'state': 'invoiced'})
    #     # print(Invoice)
    #     # Invoice.set_numero_factura
    #     # print(Invoice.nro_factura)
    #     # raise ValidationError('pos nuestro %s ' % Invoice)
    #     if not Invoice:
    #         return {}
    #
    #     return {
    #         'name': _('Customer Invoice'),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'view_id': self.env.ref('account.invoice_form').id,
    #         'res_model': 'account.invoice',
    #         'context': "{'type':'out_invoice'}",
    #         'type': 'ir.actions.act_window',
    #         'nodestroy': True,
    #         'target': 'current',
    #         'res_id': Invoice and Invoice.ids[0] or False,
    #     }
