# -*- coding: utf-8 -*-

import base64
import json
import tempfile

import requests
from odoo import exceptions, models
from OpenSSL import crypto


class Autenticacion(models.AbstractModel):
    _name = "apicontinental.autenticacion"
    _description = "Autenticación"

    def obtener_certificado(self):
        # Obtenemos certificado y pass de la BD
        company = self.env.user.company_id
        pfx = base64.b64decode(company.api_continental_cert_path)
        passphrase = company.api_continental_cert_pass.encode()

        # Ejemplo de codigo para obtener archivo de un folder
        # path = self.get_env("vbpasa_apicontinental_cert_path")
        # passphrase = self.get_env("vbpasa_apicontinental_cert_pass").encode()
        # with open(path, "rb") as f:
        #     pfx = f.read()

        p12 = crypto.load_pkcs12(pfx, passphrase)
        cert = p12.get_certificate()
        private_key = p12.get_privatekey()

        # Crea archivos temporales para los certificados PEM
        with tempfile.NamedTemporaryFile(delete=False) as cert_file:
            cert_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

        with tempfile.NamedTemporaryFile(delete=False) as key_file:
            key_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, private_key))

        return (cert_file.name, key_file.name)

    def obtener_usuario(self, name, action):
        """
        name:
            CC: Cuentas y Extractos
            PP: Pago de Proveedores
            PS: Pago de Salarios
            SC: Servicios Corporativos

        action:
            carga, consulta
        """

        data = {}
        user = ""
        password = ""
        subscription = ""
        company = self.env.user.company_id

        # Consultar cuenta
        if name == "CC":
            subscription = company.api_continental_subscription_ce
            # Para consultar se puede usar cualquier usuario
            user = company.api_continental_pp_user_carga
            password = company.api_continental_pp_pass_carga

        # pago proveedores
        elif name == "PP":
            subscription = company.api_continental_subscription_pp
            if action == "carga":
                user = company.api_continental_pp_user_carga
                password = company.api_continental_pp_pass_carga
            else:
                user = company.api_continental_pp_user_autoriza
                password = company.api_continental_pp_pass_autoriza

        # pago salarios
        elif name == "PS":
            subscription = company.api_continental_subscription_ps
            if action == "carga":
                user = company.api_continental_ps_user_carga
                password = company.api_continental_ps_pass_carga
            else:
                user = company.api_continental_ps_user_autoriza
                password = company.api_continental_ps_pass_autoriza

        # servicios corporativos
        elif name == "SC":
            # No se utiliza esta opcion
            subscription = company.api_continental_subscription_sc
            if action == "carga":
                user = company.api_continental_pp_user_carga
                password = company.api_continental_pp_pass_carga
            else:
                user = company.api_continental_pp_user_autoriza
                password = company.api_continental_pp_pass_autoriza

        data["user"] = user
        data["pass"] = password
        data["ruc"] = company.api_continental_ruc
        data["subscription"] = subscription

        return data

    def obtener_session(self, name, action, payment_id=None):
        response = None
        try:
            cert = self.obtener_certificado()
            BASE_URL = self.env.user.company_id.api_continental_url
            URL = f"{BASE_URL}/autenticarob/v1/"

            # Dependiendo del tipo de accion, se utiliza un usuario u otro
            credenciales = self.obtener_usuario(name, action)
            if not credenciales:
                raise exceptions.UserError("No se encontraron usuarios para la acción")

            headers = {
                "Usuario": credenciales["user"],
                "Password": credenciales["pass"],
                "RUC": credenciales["ruc"],
                "Subscription-Key": credenciales["subscription"],
            }
            response = requests.post(URL, headers=headers, cert=cert, timeout=22)
            # Guardamos el registro de la peticion
            self.env["apicontinental.requests_logs"].save_request("autenticar", response, None, payment_id)

            if response.status_code != 200:
                print(response.text)
                raise exceptions.UserError("No se pudo obtener el token correctamente")

            access_token = response.json()["access_token"]

            # Agregamos el token y subscription al header y retornamos la session
            session = requests.Session()
            session.cert = cert
            session.headers.update({"Content-Type": "application/json"})
            session.headers.update({"Authorization": f"Bearer {access_token}"})
            session.headers.update({"Subscription-Key": credenciales["subscription"]})

            return session
        # Agregamos exception de timeout
        except requests.exceptions.Timeout as e:
            print("timeout al obtener el token")
            print(e)
            self.env["apicontinental.requests_logs"].save_request("autenticar", response, e, payment_id)
            raise exceptions.UserError("Timeout al obtener el token")
        except Exception as e:
            print("Error al obtener el token")
            print(e)
            self.env["apicontinental.requests_logs"].save_request("autenticar", response, e, payment_id)
            raise exceptions.UserError("Error al obtener el token")

    def actualizar_credenciales(self, actualPass, newPass):
        BASE_URL = self.env.user.company_id.api_continental_url
        URL = f"{BASE_URL}/autenticarob/v1/"
        USER = self.env.user.company_id.api_continental_codigo_cliente
        RUC = self.env.user.company_id.api_continental_ruc
        session = self.obtener_session("CC", "carga")

        body = {
            "userId": USER,
            "codigoCliente": RUC,
            "passwordActual": actualPass,
            "passwordNuevo": newPass,
        }

        r = session.put(URL, json=body)
