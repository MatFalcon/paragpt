from odoo import http
from odoo.addons.web.controllers.main import Home

import babel.messages.pofile
import base64
import copy
import datetime
import functools
import glob
import hashlib
import io
import itertools
import jinja2
import json
import logging
import operator
import os
import re
import sys
import tempfile

import werkzeug
import werkzeug.exceptions
import werkzeug.utils
import werkzeug.wrappers
import werkzeug.wsgi
from collections import OrderedDict, defaultdict, Counter
from werkzeug.urls import url_encode, url_decode, iri_to_uri
from lxml import etree
import unicodedata

import odoo
import odoo.modules.registry
from odoo.api import call_kw, Environment
from odoo.modules import get_module_path, get_resource_path
from odoo.tools import image_process, topological_sort, html_escape, pycompat, ustr, apply_inheritance_specs, lazy_property, float_repr
from odoo.tools.mimetypes import guess_mimetype
from odoo.tools.translate import _
from odoo.tools.misc import str2bool, xlsxwriter, file_open
from odoo.tools.safe_eval import safe_eval, time
from odoo import http, tools, fields, exceptions
from odoo.http import content_disposition, dispatch_rpc, request, serialize_exception as _serialize_exception, Response
from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo.models import check_method_name
from odoo.service import db, security

from socket import AF_INET, SOCK_DGRAM
import sys
import pytz
import socket
import struct
import time

_logger = logging.getLogger(__name__)
db_monodb = http.db_monodb


def abort_and_redirect(url):
    r = request.httprequest
    response = werkzeug.utils.redirect(url, 302)
    response = r.app.get_response(r, response, explicit_session=False)
    werkzeug.exceptions.abort(response)


def obtener_hora_actual():
    port = 123
    buf = 1024
    address = ("aravo1.set.gov.py", port)
    msg = '\x1b' + 47 * '\0'

    # reference time (in seconds since 1900-01-01 00:00:00)
    TIME1970 = 2208988800  # 1970-01-01 00:00:00

    # connect to server
    client = socket.socket(AF_INET, SOCK_DGRAM)
    client.sendto(msg.encode('utf-8'), address)
    msg, address = client.recvfrom(buf)

    t = struct.unpack("!12I", msg)[10]

    t -= TIME1970
    return datetime.datetime.fromtimestamp(t, pytz.timezone("America/Asuncion"))


def ensure_db(redirect='/web/database/selector'):
    # This helper should be used in web client auth="none" routes
    # if those routes needs a db to work with.
    # If the heuristics does not find any database, then the users will be
    # redirected to db selector or any url specified by `redirect` argument.
    # If the db is taken out of a query parameter, it will be checked against
    # `http.db_filter()` in order to ensure it's legit and thus avoid db
    # forgering that could lead to xss attacks.
    db = request.params.get('db') and request.params.get('db').strip()

    # Ensure db is legit
    if db and db not in http.db_filter([db]):
        db = None

    if db and not request.session.db:
        # User asked a specific database on a new session.
        # That mean the nodb router has been used to find the route
        # Depending on installed module in the database, the rendering of the page
        # may depend on data injected by the database route dispatcher.
        # Thus, we redirect the user to the same page but with the session cookie set.
        # This will force using the database route dispatcher...
        r = request.httprequest
        url_redirect = werkzeug.urls.url_parse(r.base_url)
        if r.query_string:
            # in P3, request.query_string is bytes, the rest is text, can't mix them
            query_string = iri_to_uri(r.query_string)
            url_redirect = url_redirect.replace(query=query_string)
        request.session.db = db
        abort_and_redirect(url_redirect)

    # if db not provided, use the session one
    if not db and request.session.db and http.db_filter([request.session.db]):
        db = request.session.db

    # if no database provided and no database in session, use monodb
    if not db:
        db = db_monodb(request.httprequest)

    # if no db can be found til here, send to the database selector
    # the database selector will redirect to database manager if needed
    if not db:
        werkzeug.exceptions.abort(werkzeug.utils.redirect(redirect, 303))

    # always switch the session to the computed db
    if db != request.session.db:
        request.session.logout()
        abort_and_redirect(request.httprequest.url)

    request.session.db = db


class Acceso(Home):

    @http.route('/web', type='http', auth="none")
    def web_client(self, s_action=None, **kw):
        ensure_db()
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        request.uid = request.session.uid
        user_id = request.env['res.users'].sudo().browse(request.uid)
        if not user_id.has_group('base.group_system') and not user_id.has_group('control_acceso.grupo_acceso'):

            ip_address = request.httprequest.environ['REMOTE_ADDR']
            control_acceso_activado = http.request.env['ir.config_parameter'].sudo(
            ).get_param("control_acceso_activado")
            if control_acceso_activado and control_acceso_activado == "1":
                ips_admitidas = http.request.env['ir.config_parameter'].sudo(
                ).get_param("control_acceso_ips_admitidas")
                if ips_admitidas:
                    ips_admitidas = ips_admitidas.split(",")
                _logger.info(
                    "###################%s########################" % ip_address)
                if ip_address not in ips_admitidas and ips_admitidas != "*":
                    _logger.info("Bloqueo por acceso de IP")
                    return werkzeug.utils.redirect('/web/session/logout', 303)
                hi_param = http.request.env['ir.config_parameter'].sudo(
                ).get_param("control_acceso_hora_inicio")
                hf_param = http.request.env['ir.config_parameter'].sudo(
                ).get_param("control_acceso_hora_fin")
                if hi_param and hf_param:
                    hora_inicio_param = int(hi_param.split(":")[0])
                    min_inicio_param = int(hi_param.split(":")[1])
                    hora_inicio = datetime.time(
                        hora_inicio_param, min_inicio_param, 0)
                    hora_fin_param = int(hf_param.split(":")[0])
                    min_fin_param = int(hf_param.split(":")[1])
                    hora_fin = datetime.time(hora_fin_param, min_fin_param, 0)
                else:

                    raise exceptions.ValidationError(
                        "No están definidos los parámetros de horarios de acceso. Cree los parametros correctos. Contacte con su administrador")

                ahora = obtener_hora_actual().time()
                dias_admitidos = http.request.env['ir.config_parameter'].sudo().get_param("control_acceso_dia")
                if dias_admitidos:
                    dias_admitidos = dias_admitidos.split(",")
                hoy = obtener_hora_actual().date().weekday()
                if ahora < hora_inicio or ahora > hora_fin:
                    _logger.info("Bloqueo por acceso de horario")
                    _logger.info(hora_inicio)
                    _logger.info(hora_fin)
                    _logger.info(ahora)
                    return werkzeug.utils.redirect('/web/session/logout', 303)

                if str(hoy + 1) not in dias_admitidos:
                    _logger.info("Bloqueo por acceso de dia")
                    _logger.info(hora_inicio)
                    _logger.info(hora_fin)
                    _logger.info(ahora)
                    return werkzeug.utils.redirect('/web/session/logout', 303)

        try:
            context = request.env['ir.http'].webclient_rendering_context()
            response = request.render(
                'web.webclient_bootstrap', qcontext=context)
            response.headers['X-Frame-Options'] = 'DENY'
            return response
        except AccessError:
            return werkzeug.utils.redirect('/web/login?error=access')
