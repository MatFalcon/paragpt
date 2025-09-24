# -*- coding: utf-8 -*-
from odoo import models


class ConsultarCuenta(models.AbstractModel):
    _name = 'apicontinental.consultar_cuenta'
    _description = 'Pago Salario'

    def obtener_hash_cuenta(self, tipo_cuenta):
        """Consultar datos de la cuenta
        Los valores posibles para el param 'uso' son:
        TODOS, PAGO DE SALARIOS, SERVICIOS CORPORATIVOS, OPERACION DE CAMBIO, TRANSFERENCIA EXTERIOR, PAGO DE PROVEEDORES, TRANSFERENCIA INTERNA, CHEQUE GERENCIA, TRANSFERENCIA INTERBANCARIA
        """

        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/clientes/v1/consultarcuentas?uso=¨{tipo_cuenta}"
        session = self.env["apicontinental.autenticacion"].obtener_session("CC", "carga")

        r = session.get(URL)
        print(r)
        return r

    def consultar_cuenta_funcionario(self, tipo_cuenta):
        """Consultar datos de la cuenta
        Los valores posibles para el param 'uso' son:
        TODOS, PAGO DE SALARIOS, SERVICIOS CORPORATIVOS, OPERACION DE CAMBIO, TRANSFERENCIA EXTERIOR, PAGO DE PROVEEDORES, TRANSFERENCIA INTERNA, CHEQUE GERENCIA, TRANSFERENCIA INTERBANCARIA
        """

        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/clientes/v1/consultarcuentas?uso={tipo_cuenta}"
        session = self.env["apicontinental.autenticacion"].obtener_session("CC", "carga")

        r = session.get(URL)
        print(r)
        return r

    def consultar_extracto(self, hash, fromDate, toDate, nroPagina=1, cantRegistros=10):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/extracto-cuenta/v1/accounts/{hash}/transactions/normal"
        session = self.env["apicontinental.autenticacion"].obtener_session("CC", "carga")

        params = {
            'fromDate': fromDate,
            'toDate': toDate,
            'numeroPagina': nroPagina,
            'cantidadRegistro': cantRegistros
        }

        r = session.get(URL, params=params)
        return r

    def consultar_extracto_detalle(self, tipo_cuenta, id_referencia_detalle):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/extracto-cuenta/v1/{tipo_cuenta}/id/{id_referencia_detalle}"
        session = self.env["apicontinental.autenticacion"].obtener_session("CC", "carga")

        r = session.get(URL)
        print(r)
        return r
