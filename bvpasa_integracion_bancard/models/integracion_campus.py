# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
import requests
import json
import datetime
import logging

_logger = logging.getLogger(__name__)


class CursosCampus(models.Model):
    _name = 'bvpasa_integracion_bancard.cursos'
    _description = "Cursos Campus Virtual"

    course_id = fields.Integer(string="Curso ID")
    name = fields.Char(string="Nombre")
    product_id = fields.Many2one('product.product', string="Producto a facturar")


class IntegracionCampus(models.Model):
    _name = 'bvpasa_integracion_campus'
    _description = "Integración con Campus Virtual"
    _rec_name = "ticket_number"
    _order = "fecha_transaccion desc"

    fecha_transaccion = fields.Datetime(string="Fecha de Venta")
    partner_id = fields.Many2one('res.partner', string="Cliente")
    curso_ids = fields.Many2many('bvpasa_integracion_bancard.cursos', string="Cursos")
    monto = fields.Monetary(string="Importe")
    proceso_id = fields.Integer(string="Proceso ID")
    ticket_number = fields.Char(string="Nro. de Ticket")
    estado = fields.Selection(
        selection=[
            ('rechazado', 'Rechazado'),
            ('confirmado', 'Confirmado'),
            ('expirado', 'Expirado'),
            ('cancelado', 'Cancelado'),
        ],
        string='Estado',
    )
    id_pago = fields.Integer(string="ID Pago")
    currency_id = fields.Many2one('res.currency', string="Moneda")

    invoice_id = fields.Many2one('account.move', string="Factura")
    bancard_id = fields.Many2one('bvpasa_integracion_bancard', string="Bancard")

    def getToken(self):
        email = self.env['ir.config_parameter'].get_param('campus_email_login')

        password = self.env['ir.config_parameter'].get_param('campus_password_login')

        url = self.env['ir.config_parameter'].get_param('campus_url_login')

        payload = json.dumps({
            "email": email,
            "password": password
        })
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=payload)

        # _logger.warning('response campus %s', response)

        res = response.json()

        # _logger.warning('res %s', res)
        token = res['access_token']
        self.env['ir.config_parameter'].set_param('campus_token', token)

    def getRecords(self):
        url = self.env['ir.config_parameter'].get_param('campus_url_all_records')
        self.getToken()
        token = self.env['ir.config_parameter'].get_param('campus_token')

        payload = {}
        headers = {
            'Authorization': token
        }

        response = requests.request("POST", url, headers=headers, data=payload)
        # _logger.warning('response get records campus %s', response)
        res = response.json()

        # _logger.warning('res get records campus %s', res)

        for r in res:
            transacciones = r['transacciones']
            partner_id = False
            for t in transacciones:
                id_pago = t['bancard_id']
                # if self.env['bvpasa_integracion_campus'].search([('id_pago', '=', id_pago)]):
                #     _logger.warning('ya existe %s', t)
                if not self.env['bvpasa_integracion_campus'].search([('id_pago', '=', id_pago)]):
                    # _logger.warning('no hay aun')
                    if r['VpStatus'] == 'confirmado':
                        _logger.warning('r es %s', r)
                        try:
                            data = t['data']
                            if 'operation' in data:
                                data = data['operation']
                            monto = data['amount']
                            moneda = data['currency']
                            ticket_number = data['ticket_number']
                            currency_id = self.env['res.currency'].search([('name', '=', moneda)]).id
                            fecha_transaccion = r['created_at']
                            fecha_transaccion = datetime.datetime.strptime(fecha_transaccion, "%Y-%m-%dT%H:%M:%S.%fZ")
                            # fecha_transaccion = datetime.datetime(fecha_transaccion, tzinfo=datetime.timezone.utc)

                            order = r['order']
                            _logger.warning('order %s', order)
                            if not order:
                                ci = False
                                clientes = r['clientes'][0]['user_data']
                                customfields = clientes['customfields']
                                for c in customfields:
                                    if c['name'] == 'Documento de Identidad' or c['name'] == 'Documento de identidad':
                                        ci = c['value']
                                        _logger.warning('ci? %s', ci)
                                if ci:
                                    partner_id = self.env['res.partner'].search(['|', ('vat', '=', ci), ('rucdv', '=', ci)])
                                    tipo_iden = self.env['ruc.tipo.identificacion'].search([('name', '=', 'CI')], limit=1)
                                    # partner_id = self.env['res.partner'].search([('ruc', '=', ci)])
                                    if not partner_id:
                                        partner_id = self.env['res.partner'].with_context(no_vat_validation=True).create(
                                            {'tipo_identificacion': tipo_iden.id, 'ruc': ci, 'rucdv': ci,
                                             # _logger.warning('ruc al crear se carga %s', ci)
                                             # partner_id = self.env['res.partner'].create({'ruc': ci,
                                             'name': clientes[
                                                         'fullname'] + ' ' +
                                                     clientes['lastname'],
                                             'email': clientes['email']

                                             })

                            else:
                                ci = False
                                clientes = r['clientes'][0]['user_data']
                                customfields = clientes['customfields']
                                for c in customfields:
                                    if c['name'] == 'Documento de Identidad' or c['name'] == 'Documento de identidad':
                                        ci = c['value']
                                        _logger.warning('ci? %s', ci)
                                if ci:
                                    partner_id = self.env['res.partner'].search(['|', ('vat', '=', ci), ('ruc', '=', ci)])
                                    tipo_iden = self.env['ruc.tipo.identificacion'].search([('name', '=', 'CI')], limit=1)
                                    # partner_id = self.env['res.partner'].search([('ruc', '=', ci)])
                                    _logger.warning('tipo_iden %s', tipo_iden)
                                    if not partner_id:
                                        partner_id = self.env['res.partner'].with_context(no_vat_validation=True).create(
                                            {'tipo_identificacion': tipo_iden.id, 'ruc': ci, 'rucdv': ci,
                                             # _logger.warning('ruc al crear se carga %s', ci)
                                             # partner_id = self.env['res.partner'].create({'ruc': ci,
                                             'name': clientes[
                                                         'fullname'] + ' ' +
                                                     clientes['lastname'],
                                             'email': clientes['email']

                                             })
                                else:
                                    partner = order['client_billing']
                                    partner_id = self.env['res.partner'].search(
                                        ['|', ('vat', '=', partner['ruc']), ('rucdv', '=', partner['ruc'])])
                                    _logger.warning('partner vals api %s', partner)
                                    _logger.warning('ruc partner %s', partner['ruc'])
                                    # partner_id = self.env['res.partner'].search([('rucdv', '=', partner['ruc'])])
                                    _logger.info('partner id %s', partner_id)
                                    _logger.info('ruc proc %s', partner['ruc'][:-2])
                                    tipo_iden = self.env['ruc.tipo.identificacion'].search([('name', '=', 'RUC')], limit=1)

                                    if not partner_id:
                                        partner_id = self.env['res.partner'].with_context(no_vat_validation=True).create(
                                            # {'vat': partner['ruc'], 'name': partner['name']})
                                            {'tipo_identificacion': tipo_iden.id, 'ruc': partner['ruc'][:-2],
                                             # TODO: corregir variable, se coloco para hacer pruebas
                                             'rucdv': partner['ruc'], 'name': partner['name']})
                                        # ruc, dv = string.split('-')

                            courses = r['courses']
                            cursos = []
                            for c in courses:
                                cd = c['course_data']
                                curso = self.env['bvpasa_integracion_bancard.cursos'].search(
                                    [('course_id', '=', cd['id'])])
                                if not curso:
                                    curso = self.env['bvpasa_integracion_bancard.cursos'].create(
                                        {'course_id': cd['id'], 'name': cd['fullname']})
                                cursos.append(curso.id)

                            line = {
                                'fecha_transaccion': fecha_transaccion,
                                'partner_id': partner_id[0].id if partner_id else False,
                                'currency_id': currency_id,
                                'monto': monto,
                                'proceso_id': r['process_id'],
                                'id_pago': id_pago,
                                'estado': r['VpStatus'],
                                'ticket_number': ticket_number,
                                'curso_ids': [(6, 0, cursos)]
                            }

                            self.env['bvpasa_integracion_campus'].create(line)
                        except Exception as e:
                            _logger.warning(f'No se pudo crear {t["bancard_id"]}: {str(e)}')
