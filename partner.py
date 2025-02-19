# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging
import operator
from odoo.exceptions import ValidationError
from requests import Session
from datetime import datetime
_logger = logging.getLogger(__name__)

try:
    from zeep import Client
    from zeep.transports import Transport
    from zeep.plugins import HistoryPlugin
except (ImportError, IOError) as err:
    _logger.debug(err)

class PartnerFactElect(models.Model):
    _inherit = 'res.partner'
    tipo_operacion=fields.Selection(selection=[('1' ,'[B2B]acrónimo comúnmente utilizado para describir las operaciones entre empresas'),
                                    ('2' ,'[B2C]acrónimo comúnmente utilizado para describir las operaciones entre una empresa a un consumidor final'),
                                    ('3' ,'[B2G]acrónimo comúnmente utilizado para describir las operaciones entre una empresa y una entidad de gobierno'),
                                    ('4' ,'[B2F]acrónimo del tipo de operación para describir los servicios prestados por una empresa nacional a una empresa o persona física del exterior')
                                ],default='2')
    nro_casa=fields.Integer(default=0)
    tipo_documento=fields.Selection(selection=[
                                    ('1' ,'Electrónico'),
                                    ('2' ,'Impreso'),
                                    ('3' ,'Constancia Electrónica')
    ])
    naturaleza_receptor=fields.Selection(selection=[('1','contribuyente'),
                                                    ('2','no contribuyente')],default='1')
    naturaleza_vendedor=fields.Selection(selection=[('1','No contribuyente'),
                                                    ('2','Extranjero')])

    tipo_documento_receptor=fields.Selection(selection=[('1','Cédula paraguaya'),
                                                        ('2','Pasaporte'),
                                                        ('3','Cédula extranjera'),
                                                        ('4','Carnet de residencia'),
                                                        ('5','Innominado'),
                                                        ('6','Tarjeta Diplomática de exoneración fiscal'),('9','Otro')])
    tipo_documento_vendedor=fields.Selection(selection=[('1','Cédula paraguaya'),
                                                        ('2','Pasaporte'),
                                                        ('3','Cédula extranjera'),
                                                        ('4','Carnet de residencia')])
    nro_documento=fields.Char()
    country_id = fields.Many2one(default=lambda self:self.env.company.country_id)

    def get_partner_ruc_data(self):
        for rec in self:
            if not self.env.company.servidor=='produccion':
                res=super(PartnerFactElect,self).get_partner_ruc_data()
                return
            else:
                ruc = self.ruc
                today = fields.Date.today()
                # certificado=self.env['l10n.es.aeat.certificate'].search([
                #     ('company_id', '=', self.env.company.id),
                #     ('state', '=', 'active')

                certificado = self.env['firma.digital'].search([
                    ('company_id', '=', self.env.company.id),
                    ('estado', '=', 'activo')
                ], limit=1)
                # certificado = self.env['firma.digital'].search([
                #     ('company_id', '=', self.env.company.id), ('user_ids', '=', self.env.user.id),
                #     ('estado', '=', 'activo')
                # ], limit=1)
                if not certificado:
                    raise ValidationError('No se encontro ningun certificado activo en el sistema para su usuario')
                else:
                    public_crt = certificado.public_key
                    private_key = certificado.private_key
                if ruc.find('-') >= 0:
                    ruc = ruc[:ruc.find('-')]
                try:
                    int_ruc = int(ruc)
                except:
                    raise ValidationError('El RUC no debe tener letras')
                request_data = {
                    'dId': self.id,
                    'dRUCCons': ruc,
                }

                if self.env.company.servidor == 'prueba':
                    wsdl = 'http://sifen-test.set.gov.py/de/ws/consultas/consulta-ruc.wsdl?wsdl'
                else:
                    wsdl = 'https://sifen.set.gov.py/de/ws/consultas/consulta-ruc.wsdl?wsdl'
                session = Session()
                session.cert = (public_crt, private_key)
                transport = Transport(session=session)

                client = Client(wsdl, transport=transport)

                for service in client.wsdl.services.values():
                    _logger.info("service: %s" % service.name)
                    for port in service.ports.values():
                        operations = sorted(
                            port.binding._operations.values(),
                            key=operator.attrgetter('name'))

                metodo = client.get_type('ns0:tRuc')(ruc)
                metodo1 = client.get_type('ns0:dIdType')(self.id)

                fecha = datetime.now()
                result = client.service.rEnviConsRUC(metodo1, metodo)

                mje = result
                if result['dCodRes'] == '0502':
                    self.name=result['xContRUC']['dRazCons']
                    self.vat=self.rucdv
                    if result['xContRUC']['dRUCFactElec'] == 'S':
                       self.facturador_electronico=True
                    else:
                        self.facturador_electronico=False
                else:
                    raise ValidationError('RUC %s NO EXISTE EN LA BASE DE DATOS DE LA DNIT' % self.rucdv)



    @api.onchange('ci')
    def set_document_data(self):
        for rec in self:
            if rec.ci:
                rec.nro_documento = rec.ci

    @api.onchange('digitointer')
    def set_digitointer_data(self):
        for rec in self:
            if rec.digitointer:
                rec.nro_documento = rec.digitointer
            else:
                rec.nro_documento= None

    @api.onchange('country_id')
    def set_foreign_data(self):
        for rec in self:
            if rec.country_id:
                if rec.country_id != self.env.company.country_id:
                    rec.tipo_operacion = '4'
                    rec.naturaleza_receptor = '2'
                    rec.tipo_documento_receptor = '3'
                    rec.nro_documento=rec.digitointer
                else:
                    rec.tipo_operacion = '2'
                    rec.naturaleza_receptor = '1'
                    rec.tipo_documento_receptor = None
                    rec.nro_documento = rec.rucdv or rec.ci or ''