from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    payment_term_id = fields.Many2one(
        'account.payment.term',
        string='Término de Pago',
        help="Término de pago aplicado a esta orden"
    )
    
    is_credit_sale = fields.Boolean(
        string='Es Venta a Crédito',
        compute='_compute_is_credit_sale',
        store=True,
        help="Indica si esta orden es una venta a crédito"
    )

    @api.depends('payment_term_id')
    def _compute_is_credit_sale(self):
        """Determinar si la orden es una venta a crédito"""
        for order in self:
            order.is_credit_sale = bool(order.payment_term_id and 
                                       not order._is_immediate_payment_term())

    def _is_immediate_payment_term(self):
        """Verificar si el término de pago es inmediato (0 días)"""
        self.ensure_one()
        if not self.payment_term_id:
            return True
        
        # Verificar si todas las líneas del término tienen 0 días
        return all(line.nb_days == 0 for line in self.payment_term_id.line_ids)

    @api.model
    def _order_fields(self, ui_order):
        """Incluir payment_term_id en los campos de la orden"""
        order_fields = super()._order_fields(ui_order)
        order_fields['payment_term_id'] = ui_order.get('payment_term_id', False)
        return order_fields

    @api.model
    def create_from_ui(self, orders, draft=False):
        """Procesar órdenes desde la UI incluyendo términos de pago"""
        for order_data in orders:
            data = order_data.get('data', {})
            
            # Validar venta a crédito
            if 'payment_term_id' in data and data['payment_term_id']:
                self._validate_credit_sale_data(data)
        
        return super().create_from_ui(orders, draft)

    def _validate_credit_sale_data(self, order_data):
        """Validar datos de venta a crédito"""
        payment_term_id = order_data.get('payment_term_id')
        partner_id = order_data.get('partner_id')
        
        if not payment_term_id:
            return
            
        # Buscar la configuración del POS
        pos_session_id = order_data.get('pos_session_id')
        if pos_session_id:
            session = self.env['pos.session'].browse(pos_session_id)
            config = session.config_id
            
            # Validar que el POS permite ventas a crédito
            if not config.allow_credit_sales:
                raise UserError(_("Las ventas a crédito no están habilitadas en este punto de venta."))
            
            # Validar que se requiere cliente
            if config.require_customer_for_credit and not partner_id:
                raise UserError(_("Debe seleccionar un cliente para las ventas a crédito."))
            
            # Validar límite de crédito si está habilitado
            if config.credit_limit_validation and partner_id:
                self._validate_credit_limit(partner_id, order_data.get('amount_total', 0))

    def _validate_credit_limit(self, partner_id, order_amount):
        """Validar límite de crédito del cliente"""
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.exists():
            return
        


        # si no tiene seteado limite de credito
        if not partner.use_partner_credit_limit:
            return
        # Calcular credito disponible
        available_credit = partner.credit_limit - partner.credit
        
        if order_amount > available_credit:
            raise UserError(_(
                "El cliente '%s' excede su límite de crédito disponible.\n"
                "Límite: %s\n"
                "Crédito usado: %s\n"
                "Disponible: %s\n"
                "Monto de la orden: %s"
            ) % (
                partner.name,
                partner.credit_limit,
                partner.credit,
                available_credit,
                order_amount
            ))

    def _export_for_ui(self, order):
        """Exportar datos de la orden para la UI"""
        result = super()._export_for_ui(order)
        result.update({
            'payment_term_id': order.payment_term_id.id if order.payment_term_id else False,
            'is_credit_sale': order.is_credit_sale,
        })
        return result

    def _prepare_invoice_vals(self):
        """Incluir término de pago en la factura"""
        vals = super()._prepare_invoice_vals()

        if self.payment_term_id:
            vals['invoice_payment_term_id'] = self.payment_term_id.id
        
        if self.is_credit_sale:
            vals['tipo_factura'] = '2'
            
        return vals

    @api.model
    def _process_payment_lines(self, pos_order, order, pos_session, draft):
        """Procesar líneas de pago, validando método para crédito"""
        result = super()._process_payment_lines(pos_order, order, pos_session, draft)
        
        # Si es venta a crédito, validar método de pago
        if order.payment_term_id and pos_session.config_id.credit_payment_method_id:
            expected_method = pos_session.config_id.credit_payment_method_id
            
            # Verificar que al menos un pago use el método correcto
            credit_payments = order.payment_ids.filtered(
                lambda p: p.payment_method_id == expected_method
            )
            
            if not credit_payments:
                _logger.warning(
                    "Orden %s es venta a crédito pero no usa el método de pago configurado",
                    order.name
                )
        
        return result


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    def _export_for_ui(self, payment):
        """Exportar datos del pago para la UI"""
        result = super()._export_for_ui(payment)
        result.update({
            'is_credit_payment': self._is_credit_payment(),
        })
        return result

    def _is_credit_payment(self):
        """Determinar si este pago es a crédito"""
        if not self.pos_order_id.session_id.config_id.credit_payment_method_id:
            return False
        for rec in self:
            pago_credito = self.payment_method_id == self.pos_order_id.session_id.config_id.credit_payment_method_id
        return pago_credito