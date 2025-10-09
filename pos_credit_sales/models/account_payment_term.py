from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment'
    
    def _check_payment_method_id(self):
        for payment in self:
            if payment.payment_method_id not in payment.session_id.config_id.payment_method_ids or payment.payment_method_id  not in payment.session_id.config_id.credit_payment_method_id:
                raise ValidationError(_('The payment method selected is not allowed in the config of the POS session.'))


class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    available_in_pos = fields.Boolean(
        string='Disponible en POS',
        default=False,
        help="Permite que este término de pago sea usado en el Punto de Venta"
    )
    
    pos_config_ids = fields.Many2many(
        'pos.config',
        'pos_config_payment_term_rel',
        'payment_term_id',
        'pos_config_id',
        string='Configuraciones POS',
        help="Configuraciones de POS que pueden usar este término de pago"
    )

    def name_get(self):
        """Personalizar el nombre mostrado en POS"""
        result = []
        for term in self:
            name = term.name
            if term.note:
                name += f" ({term.note})"
            result.append((term.id, name))
        return result

    @api.model
    def get_terms_for_pos_config(self, pos_config_id):
        """Obtener términos de pago disponibles para una configuración POS"""
        config = self.env['pos.config'].browse(pos_config_id)
        return config.credit_payment_term_ids

    def get_days_to_pay(self):
        """Obtener días promedio para el pago"""
        self.ensure_one()
        if not self.line_ids:
            return 0
        
        total_days = sum(line.days for line in self.line_ids)
        return total_days / len(self.line_ids)

    def is_immediate_payment(self):
        """Verificar si es pago inmediato"""
        self.ensure_one()
        return all(line.days == 0 for line in self.line_ids)