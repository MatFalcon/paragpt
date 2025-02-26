from odoo import api, fields, models, exceptions

import calendar
import datetime
import os
import random
from zipfile import ZipFile


class Wizard(models.Model):
    _name = 'resolucion_90.wizard'
    _description = 'Res 90 Wizard'

    tipo_obligacion = fields.Selection(string="Tipo de obligación", selection=[(
        'mensual', '955 - Registro mensual de comprobantes'), ('anual', '956 - Registro anual de comprobantes')], default='mensual', required=True)
    mes = fields.Integer(string='Mes', default=0)
    anho = fields.Integer(string='Año', default=0, required=True)
    version = fields.Integer(string="Versión", default=1, required=True)

    @api.constrains('mes', 'anho', 'version', 'tipo_obligacion')
    def check_values(self):
        if self.tipo_obligacion == 'mensual' and (self.mes < 1 or self.mes > 12):
            raise exceptions.ValidationError('Mes incorrecto')
        if self.anho < 2021:
            raise exceptions.ValidationError('Año incorrecto')
        if self.version < 1 or self.version > 9999:
            raise exceptions.ValidationError('Versión incorrecta')

        return

    def button_generar_archivo(self):
        facturas_ventas = self.obtener_facturas(self.anho, self.mes, 'ventas')
        facturas_compras = self.obtener_facturas(self.anho, self.mes, 'compras')
        valores_ventas = self.obtener_valores_ventas(facturas_ventas)
        valores_compras = self.obtener_valores_compras(facturas_compras)
        return self.generar_archivo(self.anho, valores_ventas, valores_compras, self.version, mes=self.mes)

    @api.model
    def obtener_facturas(self, anho, mes, tipo):

        fecha_inicio = datetime.date(anho, mes, 1)
        ultimo_dia = calendar.monthrange(anho, mes)[1]
        fecha_fin = datetime.date(anho, mes, ultimo_dia)
        if tipo == 'ventas':
            ventas_invoice_ids = self.env['account.move'].search(
                [('move_type', 'in', ['out_invoice', 'in_refund']), ('journal_id.excluir_res90', '=', False), ('excluir_res90', '=', False), (
                    'invoice_date', '>=', fecha_inicio), ('invoice_date', '<=', fecha_fin), ('state', '=', 'posted'), ('company_id', '=', self.env.company.id)])
            return ventas_invoice_ids.sorted(lambda x: x.name)
        elif tipo == 'compras':
            compras_invoice_ids = self.env['account.move'].search(
                [('move_type', 'in', ['in_invoice', 'out_refund']), ('journal_id.excluir_res90', '=', False), ('excluir_res90', '=', False), (
                    'invoice_date', '>=', fecha_inicio), ('invoice_date', '<=', fecha_fin), ('state', '=', 'posted'), ('company_id', '=', self.env.company.id)])
            return compras_invoice_ids.sorted(key=lambda x: x.date)

    @api.model
    def obtener_valores_ventas(self, facturas):
        valores = []

        for i in facturas:
            reg = {
                'o1': 1,
                'o2': i.get_tipo_identificacion(),
                'o3': i.get_identificacion(),
                'o4': i.get_nombre_partner(),
                'o5': i.get_tipo_comprobante(),
                'o6': i.get_fecha_comprobante(),
                'o7': i.get_timbrado(),
                'o8': i.get_numero_comprobante(),
                'o9': i.get_monto10(),
                'o10': i.get_monto5(),
                'o11': i.get_monto_exento(),
                'o12': i.get_monto_total(),
                'o13': i.get_condicion_venta(),
                'o14': i.get_operacion_moneda_extranjera(),
                'o15': i.get_imputa_iva(),
                'o16': i.get_imputa_ire(),
                'o17': i.get_imputa_irp_rsp(),
                'o18': i.get_nro_comprobante_asociado(),
                'o19': i.get_timbrado_comprobante_asociado()
            }
            valores.append(reg)
        valores_archivo = ''
        for val in valores:
            valores_archivo = valores_archivo + "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                val.get('o1'), val.get('o2'), val.get('o3'), val.get('o4'), val.get('o5'), val.get('o6'), val.get(
                    'o7'), val.get('o8'), val.get('o9'), val.get('o10'), val.get('o11'), val.get('o12'), val.get('o13'), val.get('o14'), val.get('o15'),
                val.get('o16'), val.get('o17'), val.get('o18'), val.get('o19'))

        return valores_archivo

    @api.model
    def obtener_valores_compras(self, facturas):
        valores = []

        for i in facturas:
            reg = {
                'o1': 2,
                'o2': i.get_tipo_identificacion(),
                'o3': i.get_identificacion(),
                'o4': i.get_nombre_partner(),
                'o5': i.get_tipo_comprobante(),
                'o6': i.get_fecha_comprobante(),
                'o7': i.get_timbrado(),
                'o8': i.get_numero_comprobante(),
                'o9': i.get_monto10(),
                'o10': i.get_monto5(),
                'o11': i.get_monto_exento(),
                'o12': i.get_monto_total(),
                'o13': i.get_condicion_venta(),
                'o14': i.get_operacion_moneda_extranjera(),
                'o15': i.get_imputa_iva(),
                'o16': i.get_imputa_ire(),
                'o17': i.get_imputa_irp_rsp(),
                'o18': i.get_no_imputa(),
                'o19': i.get_nro_comprobante_asociado(),
                'o20': i.get_timbrado_comprobante_asociado()
            }
            valores.append(reg)
        valores_archivo = ''
        for val in valores:
            valores_archivo = valores_archivo + "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                val.get('o1'), val.get('o2'), val.get('o3'), val.get('o4'), val.get('o5'), val.get('o6'), val.get(
                    'o7'), val.get('o8'), val.get('o9'), val.get('o10'), val.get('o11'), val.get('o12'), val.get('o13'), val.get('o14'), val.get('o15'),
                val.get('o16'), val.get('o17'), val.get('o18'), val.get('o19'), val.get('o20'))

        return valores_archivo

    # def generar_archivo(self, anho, valores_ventas, valores_compras, version, mes=False):
    #     valores = valores.split('\n')
    #     limite_lineas = 999
    #     tandas_valores = [valores[i:i + limite_lineas] for i in range(0, len(valores), limite_lineas)]
    #
    #     if self.tipo_obligacion == 'mensual':
    #         ruc_empresa = self.env.company.vat
    #         if ruc_empresa:
    #             ruc_empresa = ruc_empresa.split('-')
    #             if ruc_empresa:
    #                 ruc_empresa = ruc_empresa[0]
    #         nombre_final_ventas = "/tmp/%s_REG_%s%s_V%s.txt" % (
    #             ruc_empresa, str(self.mes).zfill(2), self.anho, str(self.version).zfill(4))
    #         nombre_final_compras = "/tmp/%s_REG_%s%s_V%s.txt" % (
    #             ruc_empresa, str(self.mes).zfill(2), self.anho, str(self.version + 1).zfill(4))
    #     else:
    #         nombre_final = "%s_REG_%s_V%s.txt" % (
    #             self.env.company.vat, self.anho, self.version)
    #     # Ventas
    #
    #     if os.path.exists('%s' % nombre_final_ventas):
    #         os.remove('%s' % nombre_final_ventas)
    #
    #     archivo_ventas = open('%s' % nombre_final_ventas, 'w')
    #     archivo_ventas.write(valores_ventas)
    #     archivo_ventas.close()
    #
    #     # Compras
    #
    #     if os.path.exists('%s' % nombre_final_compras):
    #         os.remove('%s' % nombre_final_compras)
    #
    #     archivo_compras = open('%s' % nombre_final_compras, 'w')
    #     archivo_compras.write(valores_compras)
    #     archivo_compras.close()
    #
    #     # ZIP
    #     nombre_archivo_zip = "/tmp/%s_REG_%s%s_V%s.zip" % (
    #         ruc_empresa, str(self.mes).zfill(2), self.anho, str(self.version).zfill(4))
    #
    #     nombre_archivo_zip_hash = nombre_archivo_zip + \
    #                               '_%s' % random.getrandbits(128)
    #     zipObj = ZipFile(nombre_archivo_zip_hash, 'w')
    #     zipObj.write(nombre_final_compras)
    #     zipObj.write(nombre_final_ventas)
    #     zipObj.close()
    #
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': '/res90/download_file?file=%s&filename=%s' % (nombre_archivo_zip_hash, nombre_archivo_zip),
    #         'target': 'new',
    #
    #     }

    def generar_archivo(self, anho, valores_ventas, valores_compras, version, mes=False):
        ruc_empresa = self.env.company.vat
        if ruc_empresa:
            ruc_empresa = ruc_empresa.split('-')[0]

        if self.tipo_obligacion == 'mensual':
            # ZIP
            os.chdir('/tmp')
            nombre_archivo_zip = "%s_REG_%s%s_Z%s.zip" % (
                ruc_empresa, str(self.mes).zfill(2), self.anho, str(self.version).zfill(4))
            nombre_archivo_unico = nombre_archivo_zip + str(datetime.datetime.today())
            zipObj = ZipFile(nombre_archivo_unico, 'w')
            limite_lineas = 999

            # VENTAS

            tandas_valores_ventas = valores_ventas.split('\n')
            tandas_valores_ventas = [tandas_valores_ventas[i:i + limite_lineas] for i in range(0, len(tandas_valores_ventas), limite_lineas)]
            for c, tanda_valores in enumerate(tandas_valores_ventas):
                tanda_valores_a_escribir = '\n'.join(tanda_valores)
                nombre_archivo = "%s_REG_%s%s_V%s" % (
                    ruc_empresa,
                    str(self.mes).zfill(2),
                    self.anho,
                    str(c + self.version).rjust(4, '0')
                )
                nombre_archivo += '.txt'
                archivo = open(nombre_archivo, 'w')
                archivo.write(tanda_valores_a_escribir)
                archivo.close()
                zipObj.write(nombre_archivo)

            # COMPRAS

            tandas_valores_compras = valores_compras.split('\n')
            tandas_valores_compras = [tandas_valores_compras[i:i + limite_lineas] for i in range(0, len(tandas_valores_compras), limite_lineas)]
            for c, tanda_valores in enumerate(tandas_valores_compras):
                tanda_valores_a_escribir = '\n'.join(tanda_valores)
                nombre_archivo = "%s_REG_%s%s_C%s" % (
                    ruc_empresa,
                    str(self.mes).zfill(2),
                    self.anho,
                    str(c + self.version).rjust(4, '0')
                )
                nombre_archivo += '.txt'
                archivo = open(nombre_archivo, 'w')
                archivo.write(tanda_valores_a_escribir)
                archivo.close()
                zipObj.write(nombre_archivo)

            zipObj.close()
            return {
                'type': 'ir.actions.act_url',
                'url': '/res90/download_file?file=%s&filename=%s' % (nombre_archivo_unico, nombre_archivo_zip),
                'target': 'new',
            }
