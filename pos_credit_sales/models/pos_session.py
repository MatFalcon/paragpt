from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """Agregar account.payment.term a los modelos que se cargan en POS"""
        result = super()._pos_ui_models_to_load()
        result.append('account.payment.term')
        return result

    def _loader_params_account_payment_term(self):
        """Parámetros para cargar términos de pago"""
        domain = [('id', 'in', self.config_id.credit_payment_term_ids.ids)] if self.config_id.credit_payment_term_ids else [('id', '=', False)]
        
        return {
            'search_params': {
                'domain': domain,
                'fields': ['name', 'note', 'display_on_invoice', 'line_ids'],
            },
        }

    def _get_pos_ui_account_payment_term(self, params):
        """Procesar términos de pago con sus líneas"""
        payment_terms = self.env['account.payment.term'].search_read(**params['search_params'])
        
        for term in payment_terms:
            term_obj = self.env['account.payment.term'].browse(term['id'])
            term['line_ids'] = [{
                'days': line.nb_days,
                # 'day_of_the_month': line.day_of_the_month,
                # 'option': line.option,
                'value': line.value,
                'value_amount': line.value_amount,
            } for line in term_obj.line_ids]
        
        return payment_terms

    def _get_pos_ui_pos_config(self, params):
        """Override para incluir datos de crédito en configuración POS"""
        # Llamar al método padre para obtener la configuración base
        config = super()._get_pos_ui_pos_config(params)
        
        # Agregar datos específicos de crédito
        config.update({
            'allow_credit_sales': config.get('allow_credit_sales', False),
            'credit_payment_term_ids': config.get('credit_payment_term_ids', []),
            'credit_payment_method_id': config.get('credit_payment_method_id', False),
            'require_customer_for_credit': config.get('require_customer_for_credit', True),
            'credit_limit_validation': config.get('credit_limit_validation', True),
        })
        
        _logger.info(f"[POS Config] Crédito habilitado: {config['allow_credit_sales']}")
        
        return config

    def _pos_data_process(self, loaded_data):
        """Procesar datos adicionales para crédito"""
        super()._pos_data_process(loaded_data)
        
        # Obtener configuración POS de manera robusta
        pos_config = self._get_pos_config_from_loaded_data(loaded_data)
        if not pos_config:
            _logger.warning("No se pudo obtener configuración POS para crédito")
            return
        
        # Crear configuración de crédito
        credit_config = {
            'allow_credit_sales': pos_config.get('allow_credit_sales', False),
            'payment_terms': loaded_data.get('account.payment.term', []),
            'require_customer_for_credit': pos_config.get('require_customer_for_credit', True),
            'credit_limit_validation': pos_config.get('credit_limit_validation', True),
            'credit_payment_method': self._get_credit_payment_method_data_from_config(pos_config, loaded_data),
        }
        
        # Agregar configuración de crédito a loaded_data
        loaded_data['pos_credit_config'] = credit_config
        
        _logger.info(
            f"[POS Credit] Configuración cargada - "
            f"Habilitado: {credit_config['allow_credit_sales']}, "
            f"Términos: {len(credit_config['payment_terms'])}, "
            f"Método: {credit_config['credit_payment_method']['name'] if credit_config['credit_payment_method'] else 'None'}"
        )

    def _get_pos_config_from_loaded_data(self, loaded_data):
        """Obtener configuración POS de loaded_data de manera robusta"""
        pos_config_data = loaded_data.get('pos.config')
        
        # Caso 1: Viene como objeto único (más común en Odoo 17)
        if isinstance(pos_config_data, dict):
            return pos_config_data
        
        # Caso 2: Viene como lista con un elemento
        elif isinstance(pos_config_data, list) and len(pos_config_data) > 0:
            return pos_config_data[0]
        
        # Caso 3: No encontrado - buscar manualmente
        _logger.warning("pos.config no encontrado en loaded_data, buscando manualmente")
        try:
            config_data = self.config_id.read([
                'allow_credit_sales',
                'credit_payment_term_ids', 
                'credit_payment_method_id',
                'require_customer_for_credit',
                'credit_limit_validation',
            ])[0]
            return config_data
        except Exception as e:
            _logger.error(f"Error obteniendo configuración POS manualmente: {str(e)}")
            return None

    def _get_credit_payment_method_data_from_config(self, pos_config, loaded_data):
        """Obtener datos del método de pago de crédito"""
        method_id = pos_config.get('credit_payment_method_id')
        
        # Verificar que existe el ID del método
        if not method_id:
            return None
        
        # Manejar diferentes formatos del ID
        if isinstance(method_id, list) and len(method_id) >= 2:
            method_id = method_id[0]  # Formato (id, name)
        elif isinstance(method_id, tuple) and len(method_id) >= 2:
            method_id = method_id[0]  # Formato (id, name)
        
        # Buscar en los métodos de pago cargados
        payment_methods = loaded_data.get('pos.payment.method', [])
        for method in payment_methods:
            if method['id'] == method_id:
                return {
                    'id': method['id'],
                    'name': method['name'],
                    'type': method.get('type', ''),
                    'is_cash_count': method.get('is_cash_count', False),
                    'use_payment_terminal': method.get('use_payment_terminal', False),
                }
        
        # Si no se encuentra en los cargados, buscar directamente en BD
        try:
            method_obj = self.env['pos.payment.method'].browse(method_id)
            if method_obj.exists():
                return {
                    'id': method_obj.id,
                    'name': method_obj.name,
                    'type': method_obj.type,
                    'is_cash_count': method_obj.is_cash_count,
                    'use_payment_terminal': method_obj.use_payment_terminal,
                }
        except Exception as e:
            _logger.error(f"Error obteniendo método de pago de crédito: {str(e)}")
                
        return None