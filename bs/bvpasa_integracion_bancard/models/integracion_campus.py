# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
import requests
import json
import datetime


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

        res = response.json()
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
        res = response.json()

        for r in res:
            transacciones = r['transacciones']
            partner_id = False
            for t in transacciones:
                id_pago = t['bancard_id']
                if not self.env['bvpasa_integracion_campus'].search([('id_pago','=',id_pago)]):
                    if r['VpStatus'] == 'confirmado':
                        try:
                            data = t['data']
                            if 'operation' in data:
                                data = data['operation']
                            monto = data['amount']
                            moneda = data['currency']
                            ticket_number = data['ticket_number']
                            currency_id = self.env['res.currency'].search([('name', '=', moneda)]).id
                            fecha_transaccion = r['created_at']
                            fecha_transaccion = datetime.datetime.strptime(fecha_transaccion,"%Y-%m-%dT%H:%M:%S.%fZ")
                            #fecha_transaccion = datetime.datetime(fecha_transaccion, tzinfo=datetime.timezone.utc)

                            order = r['order']
                            if not order:
                                ci = False
                                clientes = r['clientes'][0]['user_data']
                                customfields = clientes['customfields']
                                for c in customfields:
                                    if c['name'] == 'Documento de Identidad' or c['name'] == 'Documento de identidad':
                                        ci = c['value']
                                if ci:
                                    partner_id = self.env['res.partner'].search([('vat', '=', ci)])
                                    if not partner_id:
                                        partner_id = self.env['res.partner'].create({'vat': ci,
                                                                                     'name': clientes['fullname'] + ' ' + clientes['lastname'],
                                                                                     'email':clientes['email'],
                                                                                     'obviar_validacion':True
                                                                                     })
                            else:
                                partner = order['client_billing']
                                partner_id = self.env['res.partner'].search([('vat','=',partner['ruc'])])
                                if not partner_id:
                                    partner_id = self.env['res.partner'].create({'vat':partner['ruc'],'name':partner['name'],'obviar_validacion':True})

                            courses = r['courses']
                            cursos = []
                            for c in courses:
                                cd = c['course_data']
                                curso = self.env['bvpasa_integracion_bancard.cursos'].search([('course_id', '=', cd['id'])])
                                if not curso:
                                    curso = self.env['bvpasa_integracion_bancard.cursos'].create({'course_id': cd['id'], 'name': cd['fullname']})
                                cursos.append(curso.id)

                            line = {
                                'fecha_transaccion': fecha_transaccion,
                                'partner_id': partner_id[0].id if partner_id else False,
                                'currency_id':currency_id,
                                'monto': monto,
                                'proceso_id' : r['process_id'],
                                'id_pago' : id_pago,
                                'estado': r['VpStatus'],
                                'ticket_number':ticket_number,
                                'curso_ids':[(6,0,cursos)]
                            }

                            self.env['bvpasa_integracion_campus'].create(line)
                        except:
                            print('No se pudo crear', t['bancard_id'])