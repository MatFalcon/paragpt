# -*- coding: utf-8 -*-
from odoo import fields, models, exceptions, api
from datetime import datetime, timedelta,time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.osv import expression
import time,collections
from lxml import etree
from odoo.exceptions import ValidationError




class WizardReporteCobranzas(models.TransientModel):

    _name = 'account_cobros.wizard.reporte.cobranzas'

    desde = fields.Date(string="Fecha desde")
    hasta = fields.Date(string="Fecha hasta")
    cobrador = fields.Many2one('res.users', 'Cobrador')
    orden = fields.Selection([('fecha', 'Fecha'), ('talonario', 'Talonario'), ('cobrador', 'Cobrador')],default='fecha')
    tipo_archivo= fields.Selection([('xlsx','Excel'),('pdf','PDF')])
    # cajas_ids=fields.Many2many('ruc.cajas',domain=[('state', '=', 'cerrado')])
    filtro_caja=fields.Boolean()
    filtro_cobranza=fields.Boolean()
    talonario_id = fields.Many2one('account.recibo.talonario')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self._get_default_company())
    cliente = fields.Many2one('res.partner', 'Cliente')
    detalle_factura=fields.Boolean()
    agrupar = fields.Selection([('talonario_id', 'Talonario'), ('cobrador', 'Cobrador')],default='talonario_id')


    
    def _get_default_company(self):
        return self.env.company.id


    def check_report(self):
        data = {}
        data['form'] = self.read(['desde', 'hasta', 'cobrador'])[0]
        return self._print_report(data)

    def _print_report(self, data):
        data['form'].update(self.read(['desde', 'hasta', 'cobrador', 'tipo_archivo', 'orden'])[0])
        return self.env.ref('account_cobros_py.report_cobranzas_action').report_action(self,data)

    
    def cantidad_cobros(self, desde, hasta, cobrador):
        cobros = self.env['account.recibo'].search(
            [('fecha', '>=', desde), ('fecha', '<=', hasta), ('cobrador', '=', cobrador)])
        if len(cobros) > 0:
            return len(cobros)
        else:
            return 0
    def agregar_punto_de_miles(self, numero, moneda):
        numero_con_punto = 0
        if moneda:
            if 'USD' in moneda:
                entero = int(numero)
                decimal = '{0:.2f}'.format(numero - entero)
                entero_string = '.'.join([str(int(entero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                                ::-1]
                if decimal == '0.00':
                    numero_con_punto = entero_string+',00'
                else:
                    decimal_string = str(decimal).split('.')
                    numero_con_punto = entero_string + ',' + decimal_string[1]
            else:
                numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(numero))), 3)])[
                               ::-1]
        return numero_con_punto




class ReporteCobranzas(models.AbstractModel):
    _name = 'report.account_cobros_py.report_cobranzas'

    
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        # self.model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        domain=[]
        diccionario_recibos = collections.OrderedDict()
        diccionario_recibos_dls = collections.OrderedDict()
        dic_agrupados = collections.OrderedDict()
        dic_agrupados_dls = collections.OrderedDict()

        domain+=[('company_id','=',docs.company_id.id),('state','=','confirmado')]

        if docs.desde and docs.hasta:
            domain+=[('fecha', '>=', docs.desde), ('fecha', '<=', docs.hasta)]

        if docs.talonario_id:
            domain+=[('talonario_id','=',docs.talonario_id.id)]

        if docs.cobrador:
            domain+=[('cobrador', '=', docs.cobrador.id)]

        if docs.cliente:
            domain += [('partner_id', '=', docs.cliente.id)]

        if docs.agrupar:
            orden=str(docs.agrupar)+' asc'
        else:
            orden='fecha asc'

        list_diarios=[]
        recibos=self.env['account.recibo'].search(domain, order=orden)
        recibos_gs=recibos.filtered(lambda r:r.currency_id==self.env.company.currency_id)
        recibos_dls=recibos.filtered(lambda r:r.currency_id!=self.env.company.currency_id)
        cobros=self.env['account.payment'].search([('recibo_id','in',recibos_gs.ids)])
        cobros_dls=self.env['account.payment'].search([('recibo_id','in',recibos_dls.ids)])
        lista_tipo=[ cobro.journal_id.tipo_reporte for cobro in cobros]
        lista_tipo.sort()
        lista_tipo=list(set(lista_tipo))
        lista_tipo_dls=[cobro.journal_id.tipo_reporte for cobro in cobros_dls]
        lista_tipo_dls.sort()
        lista_tipo_dls=list(set(lista_tipo_dls))
        list_diarios=[ cobro.journal_id for cobro in cobros]
        list_diarios.sort()
        list_diarios=list(set(list_diarios))
        list_diarios_dls=[ cobro.journal_id for cobro in cobros_dls]
        list_diarios_dls.sort()
        list_diarios_dls=list(set(list_diarios_dls))
        lista=[]
        talonario_actual=''
        cobrador_actual=''
        list_recibos=[]
        dic_diario=collections.OrderedDict()
        dic_diario_dls=collections.OrderedDict()
        suma=0
        for diario in list_diarios:

            b=[cobro.amount if cobro.monto_moneda_pago == 0 else cobro.monto_moneda_pago for cobro in cobros.filtered(lambda r:r.journal_id.id == diario.id and r.moneda_pago == self.env.company.currency_id ) ]

            suma=sum(b)
            dic_diario.setdefault(diario,suma)
        dic_diario=dic_diario.items()



        suma=0
        for diario in list_diarios_dls:
            a=[cobro.amount for cobro in cobros_dls.filtered(lambda r:r.journal_id.id == diario.id and (r.moneda_pago.id != self.env.company.currency_id.id or r.journal_id.retencion) )]
            suma=sum(a)
            dic_diario_dls.setdefault(diario,suma)
        dic_diario_dls=dic_diario_dls.items()
        # raise ValidationError('a')



        for recibo in recibos_gs.sorted(key=lambda r: r.name):
            lista = []
            if docs.agrupar == 'cobrador':
                if not cobrador_actual:
                    cobrador_actual=recibo.cobrador.name
                    for tipo in lista_tipo:
                        suma=sum([cobro.amount if cobro.monto_moneda_pago == 0 else cobro.monto_moneda_pago for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos.setdefault(recibo,lista)
                elif cobrador_actual == recibo.cobrador.name:
                    for tipo in lista_tipo:
                        suma=sum([cobro.amount if cobro.monto_moneda_pago == 0 else cobro.monto_moneda_pago for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos.setdefault(recibo,lista)
                else:
                    list_recibos=self.setear_lista(diccionario_recibos,lista_tipo)
                    dic_agrupados.setdefault(cobrador_actual,list_recibos)
                    list_recibos=[]
                    diccionario_recibos = collections.OrderedDict()
                    cobrador_actual = recibo.cobrador.name
                    for tipo in lista_tipo:
                        suma=sum([cobro.amount if cobro.monto_moneda_pago == 0 else cobro.monto_moneda_pago for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos.setdefault(recibo,lista)
            elif docs.agrupar == 'talonario_id':
                if not talonario_actual:
                    talonario_actual=recibo.talonario_id.name
                    for tipo in lista_tipo:
                        suma=sum([cobro.amount if cobro.monto_moneda_pago == 0 else cobro.monto_moneda_pago for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos.setdefault(recibo,lista)
                elif talonario_actual == recibo.talonario_id.name:
                    for tipo in lista_tipo:
                        suma=sum([cobro.amount if cobro.monto_moneda_pago == 0 else cobro.monto_moneda_pago for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos.setdefault(recibo,lista)
                else:
                    list_recibos=self.setear_lista(diccionario_recibos,lista_tipo)
                    dic_agrupados.setdefault(talonario_actual,list_recibos)
                    list_recibos=[]
                    diccionario_recibos = collections.OrderedDict()
                    talonario_actual = recibo.talonario_id.name
                    for tipo in lista_tipo:
                        suma=sum([cobro.amount if cobro.monto_moneda_pago == 0 else cobro.monto_moneda_pago for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos.setdefault(recibo,lista)
            else:
                for tipo in lista_tipo:
                    suma = sum([cobro.amount if cobro.monto_moneda_pago == 0 else cobro.monto_moneda_pago for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                    lista.append(suma)
                diccionario_recibos.setdefault(recibo, lista)


        if docs.agrupar:
            list_recibos = self.setear_lista(diccionario_recibos, lista_tipo)
            if talonario_actual:
                dic_agrupados.setdefault(talonario_actual, list_recibos)
            else:
                dic_agrupados.setdefault(cobrador_actual, list_recibos)
        else:
            list_recibos = self.setear_lista(diccionario_recibos, lista_tipo)
            dic_agrupados.setdefault(1, list_recibos)
        list_recibos = []
        talonario_actual=''
        cobrador_actual=''
        for recibo in recibos_dls.sorted(key=lambda r: r.name):
            lista = []
            if docs.agrupar == 'cobrador':
                if not cobrador_actual:
                    cobrador_actual=recibo.cobrador.name
                    for tipo in lista_tipo_dls:
                        suma=sum([cobro.amount for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos_dls.setdefault(recibo,lista)
                elif cobrador_actual == recibo.cobrador.name:
                    for tipo in lista_tipo_dls:
                        suma=sum([cobro.amount for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos_dls.setdefault(recibo,lista)
                else:
                    list_recibos=self.setear_lista(diccionario_recibos_dls,lista_tipo_dls)
                    dic_agrupados_dls.setdefault(cobrador_actual,list_recibos)
                    list_recibos=[]
                    diccionario_recibos_dls = collections.OrderedDict()
                    cobrador_actual = recibo.cobrador.name
                    for tipo in lista_tipo_dls:
                        suma=sum([cobro.amount for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos_dls.setdefault(recibo,lista)
            elif docs.agrupar == 'talonario_id':
                if not talonario_actual:
                    talonario_actual=recibo.talonario_id.name
                    for tipo in lista_tipo_dls:
                        suma=sum([cobro.amount for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos_dls.setdefault(recibo,lista)
                elif talonario_actual == recibo.talonario_id.name:
                    for tipo in lista_tipo_dls:
                        suma=sum([cobro.amount for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos_dls.setdefault(recibo,lista)
                else:
                    list_recibos=self.setear_lista(diccionario_recibos_dls,lista_tipo_dls)
                    dic_agrupados_dls.setdefault(talonario_actual,list_recibos)
                    list_recibos=[]
                    diccionario_recibos_dls = collections.OrderedDict()
                    talonario_actual = recibo.talonario_id.name
                    for tipo in lista_tipo_dls:
                        suma=sum([cobro.amount for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                        lista.append(suma)
                    diccionario_recibos_dls.setdefault(recibo,lista)
            else:
                for tipo in lista_tipo_dls:
                    suma = sum([cobro.amount for cobro in recibo.payment_ids if cobro.journal_id.tipo_reporte == tipo])
                    lista.append(suma)
                diccionario_recibos_dls.setdefault(recibo, lista)


        if docs.agrupar:
            list_recibos = self.setear_lista(diccionario_recibos_dls, lista_tipo_dls)
            if talonario_actual:
                dic_agrupados_dls.setdefault(talonario_actual, list_recibos)
            else:
                dic_agrupados_dls.setdefault(cobrador_actual, list_recibos)
        else:
            list_recibos = self.setear_lista(diccionario_recibos_dls, lista_tipo_dls)
            dic_agrupados_dls.setdefault(1, list_recibos)


        lista_total_tipo =[0]*len(lista_tipo)
        lista_total_tipo_dls =[0]*len(lista_tipo_dls)

        for l in dic_agrupados.values():
            lista_total_tipo = [a + b for (a, b) in zip(lista_total_tipo, l[1])]
        for l in dic_agrupados_dls.values():
            lista_total_tipo_dls = [a + b for (a, b) in zip(lista_total_tipo_dls, l[1])]


        dic_agrupados=dic_agrupados.items()
        dic_agrupados_dls=dic_agrupados_dls.items()


        # raise ValidationError('hola')

        docargs = {
            'doc_ids': self.ids,
            'doc_model': model,
            'docs': docs,
            'time': time,
            'dic_agrupados_dls': dic_agrupados_dls,
            'dic_agrupados': dic_agrupados,
            'lista_tipo': lista_tipo,
            'lista_tipo_dls': lista_tipo_dls,
            'lista_total_tipo_dls': lista_total_tipo_dls,
            'lista_total_tipo': lista_total_tipo,
            'dic_diario': dic_diario,
            'dic_diario_dls': dic_diario_dls,

        }
        return docargs

    def setear_lista(self,dic,lista_tipo):
        """

        :param dic: diccionario con el contenido del recibo mas la lista de las sumas de sus tipos
        :param lista_tipo: lista de tipos que estan habilitados para el reporte
        :return: una lista del diccionario recibos y el sub-totalizador
        """

        lista_total_tipo = [0] * len(lista_tipo)
        for l in dic.values():
            lista_total_tipo = [a + b for (a, b) in zip(lista_total_tipo, l)]
        dic=dic.items()
        list_resul=[dic,lista_total_tipo]


        return list_resul

