from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PosConfig(models.Model):
    _inherit = 'pos.config'

    # Campos para ventas a crédito
    allow_credit_sales = fields.Boolean(
        string='Permitir Ventas a Crédito',
        default=False,
        help="Habilita la opción de ventas a crédito en este punto de venta"
    )
    
    credit_payment_term_ids = fields.Many2many(
        'account.payment.term',
        'pos_config_payment_term_rel',
        'pos_config_id',
        'payment_term_id',
        string='Términos de Pago para Crédito',
        help="Términos de pago disponibles para ventas a crédito"
    )
    
    credit_payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Método de Pago a Crédito',
        help="Método de pago que se aplicará automáticamente para ventas a crédito",
        domain="[('journal_id', '=', False)]"
    )
    
    require_customer_for_credit = fields.Boolean(
        string='Requerir Cliente para Crédito',
        default=True,
        help="Obligar a seleccionar un cliente para las ventas a crédito"
    )
    
    credit_limit_validation = fields.Boolean(
        string='Validar Límite de Crédito',
        default=True,
        help="Verificar que el cliente no exceda su límite de crédito"
    )

    @api.constrains('allow_credit_sales', 'credit_payment_method_id')
    def _check_credit_payment_method(self):
        """Validar que si se permite crédito, hay un método de pago configurado"""
        for config in self:
            if config.allow_credit_sales and not config.credit_payment_method_id:
                raise ValidationError(_(
                    "Debe configurar un método de pago para las ventas a crédito "
                    "en la configuración del POS '%s'."
                ) % config.name)

    @api.constrains('allow_credit_sales', 'credit_payment_term_ids')
    def _check_credit_payment_terms(self):
        """Validar que si se permite crédito, hay términos de pago configurados"""
        for config in self:
            if config.allow_credit_sales and not config.credit_payment_term_ids:
                raise ValidationError(_(
                    "Debe configurar al menos un término de pago para las ventas a crédito "
                    "en la configuración del POS '%s'."
                ) % config.name)

    def _get_credit_data_for_pos(self):
        """Obtener datos de crédito para la interfaz POS"""
        self.ensure_one()
        
        if not self.allow_credit_sales:
            return {}
            
        # Obtener términos de pago
        payment_terms = []
        for term in self.credit_payment_term_ids:
            payment_terms.append({
                'id': term.id,
                'name': term.name,
                'note': term.note or '',
                'display_on_invoice': term.display_on_invoice,
                'line_ids': [{
                    'days': line.days,
                    'day_of_the_month': line.day_of_the_month,
                    'option': line.option,
                    'value': line.value,
                    'value_amount': line.value_amount,
                } for line in term.line_ids]
            })
        
        # Obtener método de pago
        credit_payment_method = {}
        if self.credit_payment_method_id:
            method = self.credit_payment_method_id
            credit_payment_method = {
                'id': method.id,
                'name': method.name,
                'type': method.type,
                'is_cash_count': method.is_cash_count,
                'use_payment_terminal': method.use_payment_terminal,
            }
        
        return {
            'allow_credit_sales': self.allow_credit_sales,
            'payment_terms': payment_terms,
            'credit_payment_method': credit_payment_method,
            'require_customer_for_credit': self.require_customer_for_credit,
            'credit_limit_validation': self.credit_limit_validation,
        }