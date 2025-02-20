# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools,_
from odoo.exceptions import ValidationError,UserError
from datetime import datetime



class InvoicePy(models.Model):
    _inherit = 'account.move'

    fecha_inicio_timbrado=fields.Date(compute="_get_timbrado_data",string="Fecha Inicio Timbrado")
    fecha_final_timbrado=fields.Date(compute="_get_timbrado_data",string="Fecha Final Timbrado")


    def _get_timbrado_data(self):
        for rec in self:
            if rec.talonario_factura:
                rec.fecha_inicio_timbrado = rec.talonario_factura.fecha_inicio
                rec.fecha_final_timbrado = rec.talonario_factura.fecha_final

            else:
                rec.fecha_inicio_timbrado=None
                rec.fecha_final_timbrado=None


    def get_date_formated(self):
        fecha_form=''
        for rec in self:

            if rec.date_invoice:
                fecha_form=datetime.strftime(rec.date_invoice,'%d-%m-%Y')

        return fecha_form


    def agregar_punto_de_miles_ticket(self,numero):
        numero_con_punto='.'.join([str(int(numero))[::-1][i:i+3] for i in range(0,len(str(int(numero))),3)])[::-1]
        return numero_con_punto

    def get_invoice_data(self):
        invoice = self
        datos = list()
        print(invoice)
        dato_final = 'None'
        for orden in invoice:
            datos.append(orden.nro_factura)
            datos.append(orden.talonario_factura.name)
            datos.append(orden.talonario_factura.fecha_inicio)
            datos.append(orden.talonario_factura.fecha_final)
            datos.append(orden.user_id.name)
            datos.append(orden.talonario_factura.nro_autorizacion_autoimpresor)
            datos.append(orden.partner_id.rucdv or orden.partner_id.vat)
            # dato_final = orden.talonario_factura.name
            # print(orden.talonario_factura.name)
            # print(datos)

        return datos


    @api.model
    def set_numero_factura(self):

        if self.user_id.documento_factura:
            if not self.talonario_factura:
                if not self.nro_factura:

                    self.talonario_factura=self.user_id.documento_factura
                    self.timbrado=str(self.talonario_factura.name)
                    print(self.talonario_factura)
                    suc = self.talonario_factura.suc
                    sec = self.talonario_factura.sec
                    nro = self.talonario_factura.nro_actual + 1
                    if len(suc)==1:
                        self.suc='00'+suc
                    elif len(suc)==2:
                        self.suc = '0'+suc
                    else:
                        self.suc = suc
                    # self.suc = suc
                    if len(str(nro))==1:
                        self.sec='00'+sec
                    elif len(str(nro)) == 2:
                        self.sec = '0' + sec
                    else:
                        self.sec =sec
                    # self.sec = sec
                    nro_s = str(nro)
                    cant_nro = len(nro_s)
                    if cant_nro == 1:
                        nro_final = '000000' + nro_s
                    elif cant_nro == 2:
                        nro_final = '00000' + nro_s
                    elif cant_nro == 3:
                        nro_final = '0000' + nro_s
                    elif cant_nro == 4:
                        nro_final = '000' + nro_s
                    elif cant_nro == 5:
                        nro_final = '00' + nro_s
                    elif cant_nro == 6:
                        nro_final = '0' + nro_s
                    else:
                        nro_final = nro_s
                    nro_s = str(nro)
                    self.nro = nro_final
                    self.nro_factura = str(suc) + '-' + str(sec) + '-' + str(nro_final)
                print('nro factura', self.nro_factura)
        else:
            raise UserError(_('No tiene  talonario asignado para Facturar, Favor contacte con el Responsable de asignacion de talonario'))
        if not self.tipo_comprobante:
            tipo_comprobante = self.env.ref('paraguay_backoffice.tipo_comprobante_1')
            # tipo_comprobante=self.env['ruc.tipo.documento'].search('id','=',id.id)
            self.tipo_comprobante=tipo_comprobante

        if not self.tipo_factura:
            self.tipo_factura=1

                            #------------------------------------------
                            # ----------> IMPORTANTE LEER <------------
                            # ------------------------------------------

    # FUNCION QUE PERMITE REFERENCIAR AL QWEB DE LA FACTURA DEL CLIENTE
    # COMO EJEMPLO ESTA LA FACTURA DE MERCOFLOR, DESCOMENTAR Y AGREGAR EL QWEB DEL CLIENTE

    # # @api.multi
    # def invoice_print(self):
    #     """
    #     Funcion heredada del original account.invoice para que  referencie al QWEB de la Factura
    #     """
    #
    #     self.ensure_one()
    #     return self.env.ref('mercoflor.report_factura_mercoflor').report_action(self)



