from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosCreditConfigWizard(models.TransientModel):
    _name = 'pos.credit.config.wizard'
    _description = 'Asistente de Configuración de Crédito POS'

    pos_config_id = fields.Many2one(
        'pos.config',
        string='Configuración POS',
        required=True,
        default=lambda self: self._get_default_config()
    )
    
    enable_credit_sales = fields.Boolean(
        string='Habilitar Ventas a Crédito',
        default=True
    )
    
    payment_term_ids = fields.Many2many(
        'account.payment.term',
        string='Términos de Pago',
        domain=[('available_in_pos', '=', True)]
    )
    
    create_payment_method = fields.Boolean(
        string='Crear Método de Pago "Cuenta de Cliente"',
        default=True,
        help="Crear automáticamente el método de pago si no existe"
    )
    
    require_customer = fields.Boolean(
        string='Requerir Cliente para Crédito',
        default=True
    )
    
    validate_credit_limit = fields.Boolean(
        string='Validar Límite de Crédito',
        default=True
    )
    
    journal_id = fields.Many2one(
        'account.journal',
        string='Diario para Método de Pago',
        domain=[('type', 'in', ['sale', 'general'])],
        help="Diario a usar para el método de pago de crédito"
    )

    def _get_default_config(self):
        """Obtener configuración POS por defecto"""
        return self.env.context.get('active_id')

    @api.onchange('pos_config_id')
    def _onchange_pos_config(self):
        """Cargar datos existentes al cambiar configuración"""
        if self.pos_config_id:
            config = self.pos_config_id
            self.enable_credit_sales = config.allow_credit_sales
            self.payment_term_ids = config.credit_payment_term_ids
            self.require_customer = config.require_customer_for_credit
            self.validate_credit_limit = config.credit_limit_validation

    @api.onchange('create_payment_method')
    def _onchange_create_payment_method(self):
        """Mostrar diario cuando se va a crear método de pago"""
        if self.create_payment_method and not self.journal_id:
            # Buscar diario de ventas por defecto
            journal = self.env['account.journal'].search([
                ('type', '=', 'sale'),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
            if journal:
                self.journal_id = journal

    def action_configure(self):
        """Aplicar configuración"""
        self.ensure_one()
        
        if not self.pos_config_id:
            raise UserError(_("Debe seleccionar una configuración de POS"))
        
        config = self.pos_config_id
        
        # Crear método de pago si es necesario
        payment_method = None
        if self.create_payment_method:
            payment_method = self._create_or_get_payment_method()
        else:
            # Buscar método existente
            payment_method = self.env['pos.payment.method'].search([
                ('name', '=', 'Cuenta de Cliente')
            ], limit=1)
        
        # Actualizar configuración
        vals = {
            'allow_credit_sales': self.enable_credit_sales,
            'credit_payment_term_ids': [(6, 0, self.payment_term_ids.ids)],
            'require_customer_for_credit': self.require_customer,
            'credit_limit_validation': self.validate_credit_limit,
        }
        
        if payment_method:
            vals['credit_payment_method_id'] = payment_method.id
            
            # Asegurar que el método esté en los métodos disponibles
            if payment_method.id not in config.payment_method_ids.ids:
                vals['payment_method_ids'] = [(4, payment_method.id)]
        
        config.write(vals)
        
        # Mensaje de éxito
        message = _("Configuración de crédito aplicada exitosamente")
        if self.create_payment_method and payment_method:
            message += _("\n• Método de pago 'Cuenta de Cliente' configurado")
        if self.payment_term_ids:
            message += _("\n• %d términos de pago configurados") % len(self.payment_term_ids)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("¡Configuración Completada!"),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def _create_or_get_payment_method(self):
        """Crear o obtener método de pago de cuenta de cliente"""
        # Buscar método existente
        existing_method = self.env['pos.payment.method'].search([
            ('name', '=', 'Cuenta de Cliente')
        ], limit=1)
        
        if existing_method:
            return existing_method
        
        # Crear nuevo método
        if not self.journal_id:
            raise UserError(_(
                "Debe seleccionar un diario para crear el método de pago"
            ))
        
        return self.env['pos.payment.method'].create({
            'name': 'Cuenta de Cliente',
            'journal_id': self.journal_id.id,
            'is_cash_count': False,
            'use_payment_terminal': False,
            'split_transactions': False,
        })

    def action_create_sample_terms(self):
        """Crear términos de pago de ejemplo"""
        sample_terms = [
            {'name': '15 días', 'days': 15, 'note': 'Pago a 15 días'},
            {'name': '30 días', 'days': 30, 'note': 'Pago a 30 días'},
            {'name': '60 días', 'days': 60, 'note': 'Pago a 60 días'},
            {'name': '2/10 neto 30', 'days': 30, 'note': '2% descuento si paga en 10 días'},
        ]
        
        created_terms = []
        for term_data in sample_terms:
            # Verificar si ya existe
            existing = self.env['account.payment.term'].search([
                ('name', '=', term_data['name'])
            ], limit=1)
            
            if not existing:
                if term_data['name'] == '2/10 neto 30':
                    # Término con descuento
                    term = self.env['account.payment.term'].create({
                        'name': term_data['name'],
                        'note': term_data['note'],
                        'available_in_pos': True,
                        'line_ids': [
                            (0, 0, {
                                'value': 'percent',
                                'value_amount': 100,
                                'days': 10,
                                'option': 'day_after_invoice_date',
                                'discount_percentage': 2,
                            }),
                            (0, 0, {
                                'value': 'balance',
                                'days': 30,
                                'option': 'day_after_invoice_date',
                            }),
                        ]
                    })
                else:
                    # Término simple
                    term = self.env['account.payment.term'].create({
                        'name': term_data['name'],
                        'note': term_data['note'],
                        'available_in_pos': True,
                        'line_ids': [(0, 0, {
                            'value': 'balance',
                            'days': term_data['days'],
                            'option': 'day_after_invoice_date',
                        })]
                    })
                created_terms.append(term)
        
        if created_terms:
            self.payment_term_ids = [(6, 0, created_terms)]
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Términos Creados"),
                    'message': _("%d términos de pago de ejemplo creados") % len(created_terms),
                    'type': 'success',
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Sin Cambios"),
                    'message': _("Los términos de ejemplo ya existen"),
                    'type': 'info',
                }
            }