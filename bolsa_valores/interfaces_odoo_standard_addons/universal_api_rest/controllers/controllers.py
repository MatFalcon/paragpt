# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import ensure_db, Home
import json


class UniversalAPIRest(http.Controller):

    @http.route('/api/rest/<string:model_name>/<string:function_name>', auth='user', type='http', methods=['POST'], csrf=False)
    def call_model_function(self, model_name, function_name, **kwargs):
        # universal_api_rest/controllers/controllers.py

        # Ejemplo de uso:
        # Después de autenticarse y obtener una cookie, realizar la siguiente petición POST
        # localhost:8069/api/rest/res.users/search_read
        # Con el siguiente Body
        # {"domain": [["id", "<", 30]], "fields": ["name", "login", "company_id"], "limit": 2}

        # Verificar la autenticación del usuario
        ensure_db()

        # Obtener los parámetros de la solicitud
        params = None
        if request.httprequest.data:
            params = json.loads(request.httprequest.data)

        # Buscar el modelo
        model = request.env[model_name]

        # Verificar si la función existe en el modelo
        if not hasattr(model, function_name):
            return json.dumps({'error': 'Function not found'})

        # Obtener la función del modelo
        function = getattr(model, function_name)

        # Llamar a la función con los parámetros
        if params:
            result = function(**params)
        else:
            result = function()

        # Devolver la respuesta como JSON
        return json.dumps(result)
