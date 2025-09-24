# -*- coding: utf-8 -*-

from odoo import exceptions, fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    # Campos relacionados a apicontinental
    tipo_pago = fields.Selection(
        selection_add=[
            ("interbancaria", "Continental Transferencia Interbancaria"),
            ("interna", "Continental Transferencia Interna"),
            ("cheque_gerencia", "Continental Cheque Gerencia")
        ]
    )

    # Para transferencia interbancaria
    apicontinental_listado_procedencia = fields.Many2one(
        "apicontinental.listado_procedencia_fondo", string="Procedencia de los fondos")
    apicontinental_motivo_transaccion = fields.Many2one(
        "apicontinental.listado_motivo_transaccion", string="Motivo de la transacción")

    # Para transferencia listado_apicontinental_interna
    apicontinental_numero_pago = fields.Char(string="Número de Pago")
    apicontinental_concepto = fields.Char(string="Concepto")

    # Para cheque gerencia
    apicontinental_direccion_beneficiario = fields.Char(string="Dirección del beneficiario")
    apicontinental_autorizado_nombre = fields.Char(string="Nombre del autorizado")
    apicontinental_autorizado_documento = fields.Char(string="Documento del autorizado")
    apicontinental_sucursal = fields.Many2one("apicontinental.listado_sucursal", string="Sucursal")

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()

        # Obtenemos el flujo normal de valores y agregamos los valores de apicontinental
        payment_vals.update({
            "tipo_pago": self.tipo_pago,
            "apicontinental_listado_procedencia": self.apicontinental_listado_procedencia.id,
            "apicontinental_motivo_transaccion": self.apicontinental_motivo_transaccion.id,
            "apicontinental_numero_pago": self.apicontinental_numero_pago,
            "apicontinental_concepto": self.apicontinental_concepto,
            "apicontinental_direccion_beneficiario": self.apicontinental_direccion_beneficiario,
            "apicontinental_autorizado_nombre": self.apicontinental_autorizado_nombre,
            "apicontinental_autorizado_documento": self.apicontinental_autorizado_documento,
            "apicontinental_sucursal": self.apicontinental_sucursal.id,
        })
        return payment_vals
