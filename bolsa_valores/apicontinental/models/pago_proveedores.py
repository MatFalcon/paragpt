# -*- coding: utf-8 -*-

import json

import requests
from odoo import models


class PagoProveedores(models.AbstractModel):
    _name = 'apicontinental.pago_proveedores'
    _description = 'Pago Proveedores'

    def cheque_gerencia_crear(self, payload, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/cheque/gerencia/v1/crear"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga", payment_id)

        # Ejemplo de payload
        # payload = {
        #     "monto": "",
        #     "numeroDeComprobante": "",
        #     "sucursalDePago": "",
        #     "fechaDePago": "",
        #     "concepto": "",
        #     "origen": {"cuentaHash": ""},
        #     "destino": {
        #         "numeroDePago": "",
        #         "documentoBeneficiario": "",
        #         "nombreBeneficiario": "",
        #         "direccionBeneficiario": "",
        #         "correo": "",
        #         "celular": "",
        #     },
        #     "autorizados": {
        #         "nombre": "",
        #         "documento": "",
        #     },
        # }
        r = session.post(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia cheque gerencia crear", r, None, payment_id)
        return r

    def cheque_gerencia_consultar(self, payload, nroPagina=1, cantRegistro=10, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/cheque/gerencia/v1/consultar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga", payment_id)

        params = {
            "numeroPagina": nroPagina,
            "cantidadRegistro": cantRegistro,
        }

        # Ejemplo de payload
        # payload = {
        #     "cuenta": "asAdSDXasAsasadasdasd==",
        #     "estado": "TODOS",
        #     "fechaInicio": "01/06/2021",
        #     "fechaFin": "30/06/2021",
        # }

        r = session.post(URL, params=params, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia cheque gerencia consultar", r, None, payment_id)
        return r

    def cheque_gerencia_autorizar(self, nroTicket, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/cheque/gerencia/v1/autorizar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "autoriza", payment_id)

        payload = {"numeroTicket": nroTicket}

        r = session.put(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia cheque gerencia autorizar", r, None, payment_id)
        return r

    def cheque_gerencia_anular(self, nroTicket, observacion, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/cheque/gerencia/v1/anular"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "autoriza", payment_id)

        payload = {
            "operacion": {
                "numeroTicket": nroTicket,
                "observacion": observacion,
            }
        }

        r = session.put(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia cheque gerencia anular", r, None, payment_id)
        return r

    def transferencia_interbancaria_crear(self, payload, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interbancaria/v1/crear"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga", payment_id)

        # Ejemplo de payload
        # payload = {
        #     "monto": 4000000,
        #     "motivo": "20",
        #     "fechaDePago": "31/05/2021",
        #     "procedencia": "02",
        #     "numeroFactura": "123",
        #     "origen": {"cuentaHash": "asdasdasdasdasdad=="},
        #     "destino": {
        #         "moneda": "USD",
        #         "cuentaAAcreditar": "0123465789",
        #         "titularCuenta": "NOMBRE TITULAR",
        #         "numeroDeDocumento": "12345678-9",
        #         "tipoDeDocumento": "RUC",
        #         "entidadDestino": "VISCPYPA",
        #         "celular": "09831234567",
        #         "correo": "prueba@gmail.com",
        #     },
        # }

        r = session.post(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia interbancaria crear", r, None, payment_id)
        return r

    def transferencia_interbancaria_consultar(self, payload, nroPagina=1, cantRegistro=10, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interbancaria/v1/consultar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga", payment_id)

        params = {
            "numeroPagina": nroPagina,
            "cantidadRegistro": cantRegistro,
        }

        # Ejemplo payload
        # payload = {
        #     "cuenta": "abcdeAbCDefaaaaxx==",
        #     "estado": "TODOS",
        #     "fechaInicio": "01/06/2020",
        #     "fechaFin": "30/06/2021"
        # }

        r = session.post(URL, params=params, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia interbancaria consultar", r, None, payment_id)
        return r

    def transferencia_interbancaria_autorizar(self, nroTicket, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interbancaria/v1/autorizar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "autoriza", payment_id)

        payload = {"numeroTicket": nroTicket}

        r = session.put(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia interbancaria autorizar", r, None, payment_id)
        return r

    def transferencia_interbancaria_anular(self, nroTicket, observacion, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interbancaria/v1/anular"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "autoriza", payment_id)

        payload = {
            "operacion": {
                "numeroTicket": nroTicket,
                "observacion": observacion,
            }
        }

        r = session.put(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia interbancaria anular", r, None, payment_id)
        return r

    def transferencia_internav2_crear(self, payload, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interna/v2/crear"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga", payment_id)

        # Ejemplo de payload
        # payload = {
        #     "origen": {"hashCuenta": "abcdfghijkmnPYpaPA=="},
        #     "destino": {
        #         "numeroCuenta": "012312345678",
        #         "correo": "prueba@gmail.com",
        #         "celular": "0981234567",
        #         "nombreBeneficiario": "nombre beneficiado",
        #     },
        #     "monto": 11,
        #     "fechaDePago": "26/05/2021",
        #     "numeroDePago": "44566",
        #     "numeroDeComprobante": "001-001-0000001",
        #     "concepto": "prueba de transferencia interna",
        # }

        r = session.post(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia interna crear", r, None, payment_id)
        return r

    def transferencia_internav1_consultar(self, payload, nroPagina=1, cantRegistro=10, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interna/v1/consultar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga", payment_id)

        params = {
            "numeroPagina": nroPagina,
            "cantidadRegistro": cantRegistro,
        }

        # Ejemplo de payload
        # payload = {
        #     "cuenta": "A123XAXAXAXAXAX==",
        #     "estado": "TODOS",
        #     "fechaInicio": "01/06/2021",
        #     "fechaFin": "30/06/2021",
        # }

        r = session.post(URL, params=params, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia interna consultar", r, None, payment_id)
        return r

    def transferencia_internav1_autorizar(self, nroTicket, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interna/v1/autorizar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "autoriza", payment_id)

        payload = {"numeroTicket": nroTicket}

        r = session.put(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia interna autorizar", r, None, payment_id)
        return r

    def transferencia_internav1_anular(self, nroTicket, observacion, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interna/v1/anular"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "autoriza", payment_id)

        payload = {
            "operacion": {
                "numeroTicket": nroTicket,
                "observacion": observacion,
            }
        }

        r = session.put(URL, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia interna anular", r, None, payment_id)
        return r

    def transferecia_exterior_consultar(self, payload, nroPagina=1, cantRegistro=10, payment_id=None):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/transferencia-exterior-pp/v1/consultar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga", payment_id)

        params = {
            "numeroPagina": nroPagina,
            "cantidadRegistro": cantRegistro,
        }

        # Ejemplo de payload
        # payload = {
        #     "cuenta": "TODOS",
        #     "estado": "TODOS",
        #     "fechaInicio": "01/06/2021",
        #     "fechaFin": "30/06/2021",
        # }

        r = session.post(URL, params=params, json=payload)
        self.env["apicontinental.requests_logs"].save_request("transferencia exterior consultar", r, None, payment_id)
        return r
