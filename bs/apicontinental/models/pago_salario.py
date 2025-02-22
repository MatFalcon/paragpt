# -*- coding: utf-8 -*-

import json

import requests
from odoo import models


class PagoSalario(models.AbstractModel):
    _name = 'apicontinental.pago_salario'
    _description = 'Pago Salario'

    def alta_funcionario_crear(self, payload):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/salarios/funcionarios/v1/crear"
        session = self.obtener_session("PS", "carga")

        # Ejemplo
        # payload = {
        #     "primerNombre": "NOMBRE",
        #     "segundoNombre": "NOMBRE DOS",
        #     "primerApellido": "APELLIDO",
        #     "segundoApellido": "APELLIDO DOS",
        #     "apellidoCasado": "",
        #     "direccion": "DIRECCION",
        #     "ciudad": "CIUDAD",
        #     "paisResidencia": "PY",
        #     "barrio": "BARRIO",
        #     "primerTelefono": "0999123456",
        #     "segundoTelefono": "0998765432",
        #     "tipoDocumento": "CI",
        #     "documento": "1234567",
        #     "vencimientoDocumento": "01/01/2025",
        #     "fechaNacimiento": "01/01/2000",
        #     "paisNacimiento": "PY",
        #     "ciudadNacimiento": "Asuncion",
        #     "nacionalidad": "PARAGUAYA",
        #     "estadoCivil": "Soltero",
        #     "sexo": "Masculino",
        #     "cargo": "Informática",
        #     "ingresos": "3500000",
        #     "tipoIngreso": "PYG",
        #     "correoElectronico": "prueba@gmail.com.py",
        #     "fechaIngreso": "07/09/2021",
        #     "documentacion": {
        #         "archivo": "archivoEnBase64"
        #     }
        # }

        r = session.post(URL, json=payload)
        print(r)
        return r

    def alta_funcionario_consultar(self, payload, nroPagina=1, cantRegistro=10):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago/salarios/funcionarios/v1/consultar"
        session = self.obtener_session("PS", "consulta")

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

        r = session.post(URL, params=params, payload=payload)
        print(r)
        return r

    def pago_salario_crear(self, payload):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago-salario/v1/crear"
        session = self.obtener_session("PS", "carga")

        # Ejemplo
        # payload = {
        #     "origen": {"hashCuenta": "asdasdDasdaDADasdasdadas=="},
        #     "destino": {
        #         "cuentaCredito": "012300000000",
        #         "cedulaFuncionario": "1234567",
        #     },
        #     "monto": 10000,
        #     "fechaPago": "27/05/2021",
        #     "concepto": "PP Transferencia interna",
        #     "esAguinaldo": False,
        # }

        r = session.post(URL, json=payload)
        print(r)
        return r

    def pago_salario_consultar(self, payload, nroPagina=1, cantRegistro=10):
        """
        Los posibles valores de estado son: ACTIVO, RECHAZADO, PENDIENTE, TODOS
        """
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago-salario/v1/consultar"
        session = self.obtener_session("PS", "carga")

        params = {
            "numeroPagina": nroPagina,
            "cantidadRegistro": cantRegistro,
        }

        # Ejemplo
        # payload = {
        #     "documento": "1234567",
        #     "estado": "TODOS",
        #     "fechaInicio": "21/03/2021",
        #     "fechaFin": "26/03/2021",
        # }

        r = session.post(URL, params=params, json=payload)
        print(r)
        return r

    def pago_salario_autorizar(self, nroTicket):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago-salario/v1/autorizar"
        session = self.obtener_session("PP", "autoriza")

        payload = {"numeroTicket": nroTicket}

        r = session.put(URL, json=payload)
        print(r)
        return r

    def pago_salario_anular(self, payload):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/pago-salario/v1/anular"
        session = self.obtener_session("PP", "carga")

        # Ejemplo
        # payload = {
        #     "operacion": {
        #         "numeroTicket": "1234567",
        #         "observacion": "Prueba de anulación",
        #     }
        # }

        r = session.put(URL, json=payload)
        print(r)
        return r
