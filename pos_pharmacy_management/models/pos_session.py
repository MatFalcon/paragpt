# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError

    
class PosSession(models.Model):
    _inherit = "pos.session"
    
    def _loader_params_medicine_manufacturer(self):
        return { "search_params": { "fields" : ['name', 'parent_id'] }}

    def _get_pos_ui_medicine_manufacturer(self, params):
        return self.env["medicine.manufacturer"].search_read(**params["search_params"])
    
    def _loader_params_basic_salt(self):
        return { "search_params": { "fields" : ['name'] }}

    def _get_pos_ui_basic_salt(self, params):
        return self.env["basic.salt"].search_read(**params["search_params"])
    
    def _loader_params_salt_unit(self):
        return { "search_params": { "fields" : ['salt_unit'] }}

    def _get_pos_ui_salt_unit(self, params):
        return self.env["salt.unit"].search_read(**params["search_params"])
    
    def _loader_params_medicine_salt(self):
        return { "search_params": { "fields" : ['name', 'salt', 'qty', 'unit', 'medicine_salt_ids'] }}

    def _get_pos_ui_medicine_salt(self, params):
        return self.env["medicine.salt"].search_read(**params["search_params"])

    def _loader_params_salt_composition(self):
        return { "search_params": { "fields" : ['name', 'medicine_salt_ids', 'salt_composition_ids'] }}

    def _get_pos_ui_salt_composition(self, params):
        return self.env["salt.composition"].search_read(**params["search_params"])
    
    def _loader_params_medicine_usage(self):
        return { "search_params": { "fields" : ['name', 'medicine_usage'] }}

    def _get_pos_ui_medicine_usage(self, params):
        return self.env["medicine.usage"].search_read(**params["search_params"])
    
    def _loader_params_side_effects(self):
        return { "search_params": { "fields" : ['name', 'side_effects'] }}

    def _get_pos_ui_side_effects(self, params):
        return self.env["side.effects"].search_read(**params["search_params"])
    
    def _loader_params_safety_advice(self):
        return { "search_params": { "fields" : ['name', 'safety_advice'] }}

    def _get_pos_ui_safety_advice(self, params):
        return self.env["safety.advice"].search_read(**params["search_params"])
    
    def _loader_params_chemical_class(self):
        return { "search_params": { "fields" : ['name'] }}

    def _get_pos_ui_chemical_class(self, params):
        return self.env["chemical.class"].search_read(**params["search_params"])
    
    def _loader_params_therapeutic_class(self):
        return { "search_params": { "fields" : ['name'] }}

    def _get_pos_ui_therapeutic_class(self, params):
        return self.env["therapeutic.class"].search_read(**params["search_params"])
    
    def _loader_params_action_class(self):
        return { "search_params": { "fields" : ['name'] }}

    def _get_pos_ui_action_class(self, params):
        return self.env["action.class"].search_read(**params["search_params"])

    def _loader_params_fact_box(self):
        return { "search_params": { "fields" : ['habit_forming', 'chemical_class', 'therapeutic_class', 'action_class'] }}

    def _get_pos_ui_fact_box(self, params):
        return self.env["fact.box"].search_read(**params["search_params"])

    def _loader_params_product_uom_price(self):
        return { "search_params": { "fields" : ['uom_id', 'qty', 'unit_price','price'] }}

    def _get_pos_ui_product_uom_price(self, params):
        return self.env["product.uom.price"].search_read(**params["search_params"])
    
    def _loader_params_uom_category(self):
        return { "search_params": { "fields" : ['name', 'is_medicine'] }}

    def _get_pos_ui_uom_category(self, params):
        return self.env["uom.category"].search_read(**params["search_params"])
    
    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(['manufacturer_id', 'storage', 'medicine_substitute_ids','medicine_search_term', 'is_pharma_product', 'is_medicine', 'is_prescription','salt_composition_ids', 'medicine_salt_ids', 'medicine_usage_ids', 'side_effects_ids', 'safety_advice_ids', 'fact_box_ids', 'salt_ids', 'manage_multi_uom_via_price', 'product_price_by_uom','uom_po_id'])
        return result  
    
    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].extend(['is_a_doctor', 'numero_matricula'])
        return result  

    def _pos_ui_models_to_load(self):
        models = super()._pos_ui_models_to_load()
        models_to_load = ["uom.uom", "uom.category","medicine.manufacturer", "basic.salt", "salt.unit", "medicine.salt", "salt.composition", "medicine.usage", "side.effects", "safety.advice", "chemical.class", "therapeutic.class", "action.class", "fact.box", "product.uom.price"]
        for model in models_to_load:
            if model not in models:
                models.append(model) 
        return models
    
    def getStocks(self, config_id, product_id):
        config = self.env['pos.config'].search([('id', '=', config_id)])
        location_id = config.picking_type_id.default_location_src_id.id
        stocks = self.env['stock.quant'].search_read(fields=['lot_id', 'location_id', 'quantity'], domain=[('product_id', '=', product_id), ('location_id', '=', location_id)])
        for stock in stocks:
            if(stock['lot_id']):
                lot = self.env['stock.lot'].search([('id', '=', stock['lot_id'][0])])
                if lot : stock['expiration_date'] = lot.expiration_date
        return stocks

    def _pos__get_cash_pm(self, session):
        """
        Busca el método de pago que cuenta efectivo (is_cash_count=True).
        Si falta, avisamos porque sin esto no sabemos qué diario de caja usar.
        """
        pm = session.payment_method_ids.filtered(lambda pm: pm.is_cash_count)[:1]
        if not pm:
            raise UserError(_("Configure un método de pago en efectivo (is_cash_count) en el POS."))
        return pm

    def _pos__get_cash_theoretical(self, session):
        """
        ¿Cuánto 'cree' el POS que hay en caja?
        = apertura + pagos en efectivo + cash in/out (líneas de extracto) de esta sesión.
        """
        cash_pm = self._pos__get_cash_pm(session)

        theoretical = float(session.cash_register_balance_start or 0.0)

        # Pagos en efectivo de pedidos de la sesión
        cash_payments = session.order_ids.payment_ids.filtered(
            lambda p: p.payment_method_id == cash_pm
        )
        theoretical += sum(cash_payments.mapped('amount'))

        # Líneas de extracto (cash in/out) ya registradas para esta sesión
        stmt_lines = self.env['account.bank.statement.line'].sudo().search([
            ('pos_session_id', '=', session.id),
            ('journal_id', '=', cash_pm.journal_id.id),
        ])
        theoretical += sum(stmt_lines.mapped('amount'))

        return theoretical

    def _pos__create_transfer_and_pos_cashout(self, session, excedente, label_prefix=None):
        """
        Crea:
          1) La transferencia contable (transferencias.entre.cuentas)
          2) La línea de extracto EN LA SESIÓN (cash-out) con el MISMO monto y una etiqueta
             que referencia a la transferencia (para que se vea en el reporte del POS).
        Devuelve el registro de transferencia.
        """
        cfg = session.config_id
        src_journal = cfg.pos_transfer_origin_journal_id  # Caja
        dest_journal = cfg.pos_transfer_dest_journal_id  # Banco

        if not src_journal or not dest_journal:
            raise UserError(_("Configure diarios de origen (Caja) y destino (Banco)."))

        # 1) TRANSFERENCIA CONTABLE (Caja -> Banco)
        Payment = self.env["transferencias.entre.cuentas"].sudo().with_company(session.company_id)
        payment_vals = {
            "monto": excedente,
            "currency_id": session.currency_id.id or session.company_id.currency_id.id,
            "currency_dest_id": session.currency_id.id or session.company_id.currency_id.id,
            "cuenta_origen": src_journal.id,
            "cuenta_destino": dest_journal.id,
            "fecha": fields.Date.context_today(self),
            "observacion": _("POS %s: envío excedente de caja a otra cuenta") % (session.name),
        }
        payment = Payment.create(payment_vals)
        if hasattr(payment, "confirmar"):
            payment.confirmar()

        # 2) CASH-OUT EN EL POS (línea de extracto) — MISMO MONTO, ETIQUETA AMIGABLE
        cash_pm = self._pos__get_cash_pm(session)
        etiqueta = (label_prefix or _("Transferencia a banco")) + " %s" % getattr(payment, "name", "")
        cfg = session.config_id
        src_journal = cfg.pos_transfer_origin_journal_id
        # En v17 podemos crear directamente la línea con pos_session_id + journal_id
        self.env['account.bank.statement.line'].sudo().create({
            'pos_session_id': session.id,  # liga la línea a ESTA sesión POS
            'journal_id': src_journal.id,  # diario de caja del método efectivo
            'payment_ref': etiqueta,  # se verá lindo en el reporte del POS
            'date': fields.Date.context_today(self),
            'amount': -float(excedente),  # NEGATIVO => sale efectivo (cash-out)
            'partner_id': False,
        })

        return payment

    def action_cash_transfer_from_config(self):
        """
        1) Calcula excedente (teórico - objetivo).
        2) Crea la transferencia contable y la refleja en el POS como cash-out (MISMO monto/nombre).
        3) Deja el real de cierre en el objetivo (p.ej. 500.000).
        4) Es el botón dentro del POS "Transferencia entre cuentas"
        """
        self.ensure_one()
        session = self.sudo()
        cfg = session.config_id

        if not cfg.pos_auto_transfer_enabled: #botón que se preconfigura en el pos.conf
            raise UserError(_("Auto transferencia desactivada en la configuración del POS."))

        # monto fijo
        target = float(cfg.pos_transfer_threshold or cfg.pos_fixed_opening_amount or 0.0)
        if target <= 0:
            raise UserError(_("Defina el Monto fijo (> 0)."))

        # 1) ¿Cuánto 'cree' el POS que hay ahora? (teórico)
        cash_teorico = self._pos__get_cash_theoretical(session)
        excedente = cash_teorico - target
        if excedente <= 0:
            raise UserError(_("No hay excedente para transferir."))

        # 2) Transferencia + cash-out POS con el mismo nombre (aparece en el reporte del POS)
        payment = self._pos__create_transfer_and_pos_cashout(
            session,
            excedente,
            label_prefix=_("Transferencia a banco")
        )

        # 3) Dejar declarado el REAL de cierre en el objetivo
        session.write({"cash_register_balance_end_real": target})

        return {
            "payment_id": payment.id,
            "payment_name": getattr(payment, "name", ""),
            "amount": excedente,
            "new_cash_balance": target,
        }

    def action_pos_session_close(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        """
        Cierre 'limpio':
          - Si hay excedente, crea transferencia + cash-out POS con el mismo nombre (una vez).
          - Declara real = objetivo.
        """
        bank_payment_method_diffs = bank_payment_method_diffs or {}
        for session in self.sudo():
            cfg = session.config_id
            target = float(cfg.pos_fixed_opening_amount or cfg.pos_transfer_threshold or 0.0)

            # ¿Cuánto teórico hay justo antes de cerrar?
            cash_teorico = self._pos__get_cash_theoretical(session)
            excedente = cash_teorico - target

            if excedente > 0 and cfg.pos_auto_transfer_enabled:
                # Crear una sola vez: transferencia contable + cash-out POS con MISMO nombre
                self._pos__create_transfer_and_pos_cashout(
                    session,
                    excedente,
                    label_prefix=_("Transferencia a banco (cierre)")
                )

            # Declarar REAL = objetivo (para que no haya diferencias)
            session.write({"cash_register_balance_end_real": target})

        # Ahora sí, cierre estándar
        return super().action_pos_session_close(
            balancing_account=balancing_account,
            amount_to_balance=amount_to_balance,
            bank_payment_method_diffs=bank_payment_method_diffs,
        )
    @api.model
    def get_available_locations_for_pos_product(self, product_id):
        """Wrapper para obtener ubicaciones desde el POS"""
        # cuando seleccionamos un producto con lote
        print("ENTRA EN get_available_locations_for_pos_product")
        return self.env['stock.lot'].get_available_locations_for_product(product_id)
    @api.model
    def get_lots_by_location(self, product_id, location_id):
        """Wrapper para obtener lotes por ubicación desde el POS"""
        # despues de seleccionar una ubicacion en el pos
        print("ENTRA en get_lots_by_location")
        return self.env['stock.lot'].get_lots_by_location_and_product(product_id, location_id)
    @api.model
    def get_lot_assignment_proposal(self, product_id, requested_qty, preferred_locations=None):
        """Wrapper para obtener propuesta de asignación desde el POS"""
        return self.env['stock.lot'].propose_lot_assignment(product_id, requested_qty, preferred_locations)