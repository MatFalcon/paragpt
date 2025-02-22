# -*- coding: utf-8 -*-

import json

import requests
from odoo import models


class ServicioCorporativo(models.AbstractModel):
    _name = 'apicontinental.servicio_corporativo'
    _description = 'Servicio Corporativo'

    def transferencia_operaciones_cambio_crear(self, payload):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interbancaria/v1/crear"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga")

        # Ejemplo de payload
        # payload = {
        #     "montoDebitar": 14000000,
        #     "fecha": "03/09/2021",
        #     "origen": {
        #         "hashCuenta": "ASDASDASDASDADFDGFSDFSDFA=="
        #     },
        #     "destino": {
        #         "cuentaCredito": "002612345678",
        #         "moneda": "USD"
        #     },
        #     "mejoraCotizacion": {
        #         "esMejora": false,
        #         "montoCotizacion": 0,
        #         "comentarioCotizacion": ""
        #     }
        # }

        r = session.post(URL, json=payload)
        print(r)
        return r

    def transferencia_operaciones_cambio_consultar(self, payload, nroPagina=1, cantRegistro=10):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/cuentas/operaciones-de-cambio/v1/Consultar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga")

        params = {
            "numeroPagina": nroPagina,
            "cantidadRegistro": cantRegistro,
        }

        # Ejemplo payload
        # payload = {
        #     "hashCuenta": "AXAXAXAXAXA123==",
        #     "estado": "TODOS",
        #     "fechaInicio": "26/04/2021",
        #     "fechaFin": "27/04/2021"
        # }

        r = session.post(URL, params=params, json=payload)
        print(r)
        return r

    def transferencia_operaciones_cambio_autorizar(self, nroTicket):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/proveedores/transferencia/interbancaria/v1/autorizar"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "autoriza")

        payload = {"numeroTicket": nroTicket}

        r = session.put(URL, json=payload)
        print(r)
        return r

    def transferencia_operaciones_cambio_anular(self, nroTicket, observacion):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/cuentas/operaciones-de-cambio/v1/Crear"
        session = self.env["apicontinental.autenticacion"].obtener_session("PP", "carga")

        payload = {
            "operacion": {
                "numeroTicket": nroTicket,
                "observacion": observacion,
            }
        }

        r = session.put(URL, json=payload)
        print(r)
        return r
