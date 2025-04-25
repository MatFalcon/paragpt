# -*- coding: utf-8 -*-
import re
import pytz
import logging
import psycopg2
from datetime import datetime
from collections import defaultdict
from odoo.osv.expression import AND

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
                else:
                    record.talla = False
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
        print("########## INVOICE VALS ##########")
        print(vals)
        self.ensure_one()


        if self.amount_total < 0:
            talonario = self.config_id.talonario_nota_credito
            vals['timbrado'] = str(self.config_id.talonario_nota_credito.name)
            timbrado_obj = self.config_id.talonario_nota_credito
            tipo_comprobante = self.env.ref('paraguay_backoffice.tipo_comprobante_3').id

        else:
            talonario =  self.config_id.talonario_factura
            vals['timbrado'] = str(self.config_id.talonario_factura.name)
            tipo_comprobante = self.env.ref('paraguay_backoffice.tipo_comprobante_1').id
            timbrado_obj = self.config_id.talonario_factura


        vals['talonario_factura'] = talonario.id
        vals['suc'] = talonario.suc
        vals['sec'] = talonario.sec
        nro=str(talonario.get_nro_and_ser_next()).zfill(7)
        vals['nro'] = nro
        vals['nro_factura'] = str(talonario.suc) + '-' + str(talonario.sec) + '-' + str(nro)
        print("Nro inicial buscando", vals['nro_factura'])
        # validar el nro de la factura

        facturas = self.env['account.move'].search(
            [['move_type', '=', vals['move_type']], ['timbrado', '=', vals['timbrado']],
            ['nro_factura', '=', vals['nro_factura']],
             ['tipo_comprobante.codigo_rg90', 'in', (109, 110, 111, 101)]])
        # ira sumando hasta que encuentre un nro valido y dentro del rango configurado en el timbrado
        while facturas:
            print("Ya existe", vals['nro_factura'])
            nro = int(nro) + 1
            if nro > timbrado_obj.nro_fin:
                raise ValidationError(
                    f'El numero de factura esta fuera de rango de su talonario favor verificar \nActual: {nro} Nro Final: {timbrado_obj.nro_fin}')
            print(str(nro).zfill(7))
            nro = str(nro).zfill(7)
            vals['nro'] = str(nro).zfill(7)
            vals['nro_factura'] = str(talonario.suc) + '-' + str(talonario.sec) + '-' + str(nro)
            print("Nuevo nro", vals['nro_factura'])
            facturas = self.env['account.move'].search(
                [['move_type', '=', vals['move_type']], ['timbrado', '=', vals['timbrado']],
                 ['nro_factura', '=', vals['nro_factura']],
                 ['tipo_comprobante.codigo_rg90', 'in', (109, 110, 111, 101)]])


        #timbrado_obj.nro_actual = nro
        vals['tipo_factura'] = '1'
        vals['tipo_comprobante'] = tipo_comprobante

        #sle_order = self.env['sale.order'].search([('pos_order_ids', 'in', self.id)], limit=1)

        #vals['invoice_user_id'] = 1#sale_order.user_id.id  # Usa el vendedor original

        # Depuración (ver si entra en la función)
        _logger = models.logging.getLogger(__name__)
        _logger.info("########## INVOICE VALS MODIFICADO ##########")
        #
        #print(vals)
        _logger.info(vals)


        return vals


    ##### Funcion de models/pos_order en point_of_sale ####
    # Si se cargo un pedido para la venta, con un usuario, setea ese mismo
    # usuario en la factura independientemente del cajero en pdv
    def _generate_pos_order_invoice(self):
        moves = self.env['account.move']
        print("_generate_pos_order_invoice desde pos_paraguay")
        for order in self:
            # Si ya tiene una factura, continuar
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            move_vals = order._prepare_invoice_vals()
            new_move = order._create_invoice(move_vals)


            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            new_move.sudo().with_company(order.company_id).with_context(skip_invoice_sync=True)._post()

            # Buscar el pedido de venta relacionado si hubiere alguno
            sale_order = self.env["sale.order"].search([('pos_order_line_ids', 'in', order.lines.ids)], limit=1)
            # si hay pedido de venta o se cargo uno se setea el usuario que cargo el pedido como el vendedor de la fact
            if sale_order and sale_order.user_id:
                new_move.invoice_user_id = sale_order.user_id
                new_move.sale_order_id = sale_order.id # setea el campo Pedido de Venta asignado Manualmente

            moves += new_move
            payment_moves = order._apply_invoice_payments(order.session_id.state == 'closed')


            if self.env.context.get('generate_pdf', True):
                template = self.env.ref(new_move._get_mail_template())
                new_move.with_context(skip_invoice_sync=True)._generate_pdf_and_send_invoice(template)

            if order.session_id.state == 'closed':
                order._create_misc_reversal_move(payment_moves)

        if not moves:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': moves.ids[0] if moves else False,
        }

    #Esta funcion pasa los datos de la orden en js
    def _export_for_ui(self, order):
        timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        return {
            'lines': [[0, 0, line] for line in order.lines.export_for_ui()],
            'statement_ids': [[0, 0, payment] for payment in order.payment_ids.export_for_ui()],
            'name': order.pos_reference,
            'uid': re.search('([0-9-]){14,}', order.pos_reference).group(0),
            'amount_paid': order.amount_paid,
            'amount_total': order.amount_total,
            'amount_tax': order.amount_tax,
            'amount_return': order.amount_return,
            'pos_session_id': order.session_id.id,
            'pricelist_id': order.pricelist_id.id,
            'partner_id': order.partner_id.id,
            'user_id': order.user_id.id,
            'sequence_number': order.sequence_number,
            'date_order': str(order.date_order.astimezone(timezone)),
            'fiscal_position_id': order.fiscal_position_id.id,
            'to_invoice': order.to_invoice,
            'shipping_date': order.shipping_date,
            'state': order.state,
            'account_move': order.account_move and {
                'id': order.account_move.id,
                'name': order.account_move.name,
            } or False,# le aniadi esta parte para que me retorne tambien el nro de la factura

            'id': order.id,
            'is_tipped': order.is_tipped,
            'tip_amount': order.tip_amount,
            'access_token': order.access_token,
            'ticket_code': order.ticket_code,
            'last_order_preparation_change': order.last_order_preparation_change,
        }

    @api.model
    def search_paid_order_ids(self, config_id, domain, limit, offset):
        """Herencia de la funcion search_paid_order_ids de point_of_sale
            Se agrega el dominio de config_id para que se filtre por el punto de venta
        """
        _logger.info("search_paid_order_ids desde pos_paraguay (limitando los resultados por config_id)")
        default_domain = [('state', '!=', 'draft'), ('state', '!=', 'cancel')]
        if domain == []:
            real_domain = AND([[['config_id', '=', config_id]], default_domain])
        else:
            real_domain = AND([domain, [['config_id', '=', config_id]], default_domain])
        orders = self.search(real_domain, limit=limit, offset=offset)
        # We clean here the orders that does not have the same currency.
        # As we cannot use currency_id in the domain (because it is not a stored field),
        # we must do it after the search.
        pos_config = self.env['pos.config'].browse(config_id)
        orders = orders.filtered(lambda order: order.currency_id == pos_config.currency_id)
        orderlines = self.env['pos.order.line'].search(['|', ('refunded_orderline_id.order_id', 'in', orders.ids), ('order_id', 'in', orders.ids)])

        # We will return to the frontend the ids and the date of their last modification
        # so that it can compare to the last time it fetched the orders and can ask to fetch
        # orders that are not up-to-date.
        # The date of their last modification is either the last time one of its orderline has changed,
        # or the last time a refunded orderline related to it has changed.
        orders_info = defaultdict(lambda: datetime.min)
        for orderline in orderlines:
            key_order = orderline.order_id.id if orderline.order_id in orders \
                            else orderline.refunded_orderline_id.order_id.id
            if orders_info[key_order] < orderline.write_date:
                orders_info[key_order] = orderline.write_date
        totalCount = self.search_count(real_domain)
        return {'ordersInfo': list(orders_info.items())[::-1], 'totalCount': totalCount}
