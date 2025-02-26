from odoo import http
from odoo.http import request, Response, JsonRequest
from odoo.tools import date_utils
import json

class JsonRequestNew(JsonRequest):

    def _json_response(self, result=None, error=None):

        response = {
            'jsonrpc': '2.0',
            'id': self.jsonrequest.get('id')
        }
        if error is not None:
            response['error'] = error
        if result is not None:
            response['result'] = result
            if isinstance(result, dict):
                if result.get('forma_pago') is not None:
                    response = []
                    response.append(result)

        responseData = super(JsonRequestNew, self)._json_response(result=result,error=error)


        mime = 'application/json'
        body = json.dumps(response, default=date_utils.json_default)

        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )

class RootNew(http.Root):

    def get_request(self, httprequest):

        # deduce type of request

        jsonResponse = super(RootNew, self).get_request(httprequest=httprequest)

        if httprequest.mimetype in ("application/json", "application/json-rpc"):
            return JsonRequestNew(httprequest)
        else:
            return jsonResponse

http.root = RootNew()