# -*- coding: utf-8 -*-

from odoo import exceptions, fields, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    # Campos relacionados a apicontinental
    tipo_pago = fields.Selection(
        selection_add=[
            ("interbancaria", "Continental Transferencia Interbancaria"),
            ("interna", "Continental Transferencia Interna"),
            ("cheque_gerencia", "Continental Cheque Gerencia")
        ]
    )
    apicontinental_numero_ticket = fields.Char(string="Número de Ticket")
    apicontinental_comprobante = fields.Char(string="Comprobante")
    is_continental = fields.Boolean(string="Es una cuenta de Continental", default=False)
    apicontinental_state = fields.Selection(
        string="Estado APIContinental",
        selection=[
            ("draft", "Borrador"),
            ("pending", "Pendiente"),
            ("posted", "Aprobado"),
            ("cancel", "Anulado"),
            ("error", "Error")
        ],
        default="draft"
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

    # Agregamos campos de auditoria para guardar request y response del API
    apicontinental_motivo_anulacion = fields.Char(string="Motivo de anulación")
    apicontinental_request = fields.Text(string="Solicitud")
    apicontinental_response = fields.Text(string="Respuesta")
    apicontinental_autorizacion_response = fields.Text(string="Respuesta autorización")
    apicontinental_anulacion_response = fields.Text(string="Respuesta anulación")
    apicontinental_error = fields.Boolean(string="Error", default=False)
    apicontinental_transferencia_id = fields.Many2one(
        "apicontinental.transferencias.estado", string="Estado Transferencia")
    apicontinental_requests = fields.One2many(
        "apicontinental.requests_logs", "payment", string="Requests")

    def action_post(self):
        res = super(AccountPayment, self).action_post()

        for record in self:
            # Intentamos crear una solicitud en el API de Continental
            record.crear_solicitud()

        return res

    def validar_solicitud(self):
        if self.tipo_pago not in ["interbancaria", "interna", "cheque_gerencia"]:
            return False

        # Si es pago entrante, no se envia al API CONTINENTAL
        if self.payment_type == "inbound":
            return False

        # Si es transferencia interna, entre cuentas de la misma compañia, no se envia al API CONTINENTAL
        if self.is_internal_transfer:
            return False

        # Verificamos si tiene el grupo de cargar_pagos
        if not self.env.user.has_group("integracion_api_continental.cargar_transacciones"):
            raise exceptions.ValidationError("El usuario no tiene permisos para cargar pagos del API de CONTINENTAL")

        # El nro de recibo es obligatorio
        if not self.nro_recibo:
            raise exceptions.ValidationError("El número de recibo es un campo obligatorio")

        # El diario debe tener un hash asociado
        if not self.journal_id.api_continental_hash:
            raise exceptions.ValidationError("El diario debe tener un hash asociado para poder realizar pagos")

        # El parner es obligatorio
        if not self.partner_id:
            raise exceptions.ValidationError("El proveedor es un campo obligatorio")

        # El proveedor debe tener una cuenta bancaria asociada
        if not self.partner_id.bank_ids:
            raise exceptions.ValidationError("El proveedor debe tener una cuenta bancaria asociada")

        # Para interbancaria la cuenta bancaria debe tener un BIC asociado
        if self.tipo_pago == "interbancaria":
            if not self.partner_id.bank_ids[0].bank_id.bic:
                raise exceptions.ValidationError("La cuenta bancaria del proveedor debe tener un BIC asociado")
        
        if not self.clean_number(self.partner_id.mobile):
            raise exceptions.ValidationError("El proveedor debe tener un número de movil asociado")

        if len(self.clean_number(self.partner_id.mobile)) != 10:
            raise exceptions.ValidationError("El número de movil debe tener 10 digitos (Formato: 0981222333)")

        if not self.partner_id.email:
            raise exceptions.ValidationError("El proveedor debe tener un email asociado")

        return True

    def crear_solicitud(self):
        """
        Metodo para crear una solicitud de pago en el API del banco Continental
        Se puede llamar desde el proceso de pago o de forma independiente, toma los datos asociados a account_payment
        """
        # Si la validacion pasa correctamente, se envia al API CONTINENTAL
        if self.validar_solicitud():
            self.is_continental = True

            # Verificamos los tipos de transferencias
            if self.tipo_pago == "interbancaria":
                self.transferencia_interbancaria()

            if self.tipo_pago == "interna":
                self.transferencia_interna()

            if self.tipo_pago == "cheque_gerencia":
                self.cheque_gerencia()

    def transferencia_interbancaria(self):
        try:
            # Preparamos el payload
            payload = {
                "monto": self.amount,
                "motivo": self.apicontinental_motivo_transaccion.code,
                "fechaDePago": self.date.strftime("%d/%m/%Y"),
                "procedencia": self.apicontinental_listado_procedencia.code,
                "numeroFactura": self.nro_recibo,
                "origen": {"cuentaHash": self.journal_id.api_continental_hash},
                "destino": {
                    "moneda": self.currency_id.name,
                    "cuentaAAcreditar": self.partner_id.bank_ids[0].acc_number,
                    "titularCuenta": self.partner_id.name,
                    "numeroDeDocumento": self.partner_id.vat,
                    "tipoDeDocumento": self.partner_id.tipo_documento,
                    "entidadDestino": self.partner_id.bank_ids[0].bank_id.bic,
                    "celular": self.clean_number(self.partner_id.mobile),
                    "correo": self.partner_id.email,
                },
            }

            self.apicontinental_request = str(payload)
            result = self.env["apicontinental.pago_proveedores"].transferencia_interbancaria_crear(payload, self.id)
            self.apicontinental_response = result.text

            # Si hay error al crear la transferencia interbancaria, se marca el pago como error
            if result.status_code != 201:
                self.apicontinental_error = True
                self.apicontinental_state = "error"
                self._cr.commit()

                raise exceptions.ValidationError("Error al crear transferencia interbancaria")

            self.apicontinental_numero_ticket = result.json()["numeroTicket"]
            self.apicontinental_state = "pending"

            # Persistimos todos los datos hasta aqui
            self._cr.commit()

            # Guardamos el comprobante
            self.consultar_comprobante()

        except Exception as e:
            print("Error al crear transferencia interbancaria")
            print(e)
            raise exceptions.ValidationError(e.args[0])

    def transferencia_interna(self):
        try:
            # Preparamos el payload
            payload = {
                "monto": self.amount,
                "fechaDePago": self.date.strftime("%d/%m/%Y"),
                "numeroDePago": self.apicontinental_numero_pago,
                "concepto": self.apicontinental_concepto,
                "numeroDeComprobante": self.nro_recibo,
                "origen": {"hashCuenta": self.journal_id.api_continental_hash},
                "destino": {
                    "numeroCuenta": self.partner_id.bank_ids[0].acc_number,
                    "nombreBeneficiario": self.partner_id.name,
                    "celular": self.clean_number(self.partner_id.mobile),
                    "correo": self.partner_id.email,
                },
            }

            self.apicontinental_request = str(payload)
            result = self.env["apicontinental.pago_proveedores"].transferencia_internav2_crear(payload, self.id)
            self.apicontinental_response = result.text

            # Si hay error al crear la transferencia interna, se marca el pago como error
            if result.status_code != 201:
                self.apicontinental_error = True
                self.apicontinental_state = "error"
                raise exceptions.ValidationError("Error al crear transferencia interna")

            self.apicontinental_numero_ticket = result.json()["numeroTicket"]
            self.apicontinental_state = "pending"

            # Persistimos todos los datos hasta aqui
            self._cr.commit()

            # Guardamos el comprobante
            self.consultar_comprobante()

        except Exception as e:
            print("Error al crear transferencia interna")
            print(e)
            raise exceptions.ValidationError(e[0])

    def cheque_gerencia(self):
        try:
            # Preparamos el payload
            payload = {
                "monto": self.amount,
                "numeroDeComprobante": self.nro_recibo,
                "sucursalDePago": self.apicontinental_sucursal.code,
                "fechaDePago": self.date.strftime("%d/%m/%Y"),
                "concepto": self.apicontinental_concepto,
                "origen": {"cuentaHash": self.journal_id.api_continental_hash},
                "destino": {
                    "numeroDePago": self.apicontinental_numero_pago,
                    "documentoBeneficiario": self.partner_id.vat,
                    "nombreBeneficiario": self.partner_id.name,
                    "direccionBeneficiario": self.apicontinental_direccion_beneficiario,
                    "correo": self.partner_id.email,
                    "celular": self.clean_number(self.partner_id.mobile),
                },
                "autorizados": [
                    {
                        "nombre": self.apicontinental_autorizado_nombre,
                        "documento": self.apicontinental_autorizado_documento
                    }
                ]
            }

            self.apicontinental_request = str(payload)
            result = self.env["apicontinental.pago_proveedores"].cheque_gerencia_crear(payload, self.id)
            self.apicontinental_response = result.text

            # Si hay error al crear el cheque de gerencia, se marca el pago como error
            if result.status_code != 201:
                self.apicontinental_error = True
                raise exceptions.ValidationError("Error al crear cheque gerencia")

            self.apicontinental_numero_ticket = result.json()["numeroTicket"]
            self.apicontinental_state = "pending"

            # Persistimos todos los datos hasta aqui
            self._cr.commit()

            # Guardamos el comprobante
            self.consultar_comprobante()

        except Exception as e:
            print("Error al crear cheque de gerencia")
            print(e)
            raise exceptions.ValidationError(e[0])

    def autorizar_transferencia(self):
        # Verificamos si tiene el grupo de cargar_pagos
        if not self.env.user.has_group("integracion_api_continental.autorizar_transacciones"):
            raise exceptions.ValidationError("El usuario no tiene permisos para autorizar el pago")

        if not self.apicontinental_numero_ticket:
            raise exceptions.ValidationError("No existe número de ticket para el pago")

        nro_ticket = self.apicontinental_numero_ticket

        if self.tipo_pago == "interbancaria":
            result = self.env["apicontinental.pago_proveedores"].transferencia_interbancaria_autorizar(nro_ticket, self.id)

        if self.tipo_pago == "interna":
            result = self.env["apicontinental.pago_proveedores"].transferencia_internav1_autorizar(nro_ticket, self.id)

        if self.tipo_pago == "cheque_gerencia":
            result = self.env["apicontinental.pago_proveedores"].cheque_gerencia_autorizar(nro_ticket, self.id)

        self.apicontinental_autorizacion_response = result.text

        if result.status_code == 200:
            self.apicontinental_state = "posted"
            self.consultar_comprobante()
        else:
            raise exceptions.ValidationError("Error al aprobar la transferencia")

    def anular_transferencia(self):
        # Verificamos si tiene el grupo de cargar_pagos
        if not self.env.user.has_group("integracion_api_continental.anular_transacciones"):
            raise exceptions.ValidationError("El usuario no tiene permisos para anular el pago")

        if not self.apicontinental_numero_ticket:
            raise exceptions.ValidationError("No existe número de ticket para el pago")

        self.apicontinental_motivo_anulacion = "Pago anulado"
        params = self.apicontinental_numero_ticket, self.apicontinental_motivo_anulacion, self.id

        if self.tipo_pago == "interbancaria":
            result = self.env["apicontinental.pago_proveedores"].transferencia_interbancaria_anular(*params)

        if self.tipo_pago == "interna":
            result = self.env["apicontinental.pago_proveedores"].transferencia_internav1_anular(*params)

        if self.tipo_pago == "cheque_gerencia":
            result = self.env["apicontinental.pago_proveedores"].cheque_gerencia_anular(*params)

        self.apicontinental_anulacion_response = result.text

        if result.status_code == 200:
            self.apicontinental_state = "cancel"
            self.consultar_comprobante()
        else:
            raise exceptions.ValidationError("Error al anular la transferencia")

    def consultar_comprobante(self, estado=None):
        fecha_inicio = self.date.strftime("%d/%m/%Y")
        fecha_fin = self.date.strftime("%d/%m/%Y")
        hash_api = self.journal_id.api_continental_hash
        nro_ticket = self.apicontinental_numero_ticket
        partner_id = self.partner_id
        estado = "TODOS" if not estado else estado
        tipo_pago = self.tipo_pago
        payment_id = self.id

        result = self.env["apicontinental.transferencias.estado"].consultar_estado_transferencia(
            hash_api, nro_ticket, partner_id, fecha_inicio, fecha_fin, estado, tipo_pago, payment_id)

        if result:
            self.sudo().write({
                'apicontinental_transferencia_id': result.id,
                'apicontinental_comprobante': result.comprobante,
            })

            # Guardamos en el memo el comprobante
            if self.ref:
                self.ref += result.comprobante
            else:
                self.ref = result.comprobante

    def clean_number(self, number):
        if number:
            # Quitamos espacios y caracter +
            _number = number.replace(" ", "").replace("+", "")
            # Si empieza con 595, reemplazamos por 0
            if _number.startswith("595"):
                _number = "0" + _number[3:]

            return _number
        else:
            return ""
