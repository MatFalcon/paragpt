# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
from num2words import num2words

from odoo.tools import float_round, round


class factura(models.Model):
    _inherit = "account.recibo"
    domicilio_vendedor_proveedor = fields.Char(string="Domicilio del vendedor o proveedor")
    domicilio_transaccion = fields.Char(string="Domicilio del lugar de transacción")
    cedula_identidad = fields.Char(string="Cedula de Identidad")

    fecha = fields.Date(string="Fecha")
    fecha_formateada = fields.Char(
        string="Fecha en Palabras",
        compute="_compute_fecha_formateada"
    )

    meses = {
        1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
        5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
        9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
    }

    @api.depends("fecha")
    def _compute_fecha_formateada(self):
        for record in self:
            if record.fecha:
                dia = record.fecha.day
                mes = record.fecha.month
                anio = record.fecha.year
                record.fecha_formateada = f"{dia} de {self.meses[mes]} de {anio}"
            else:
                record.fecha_formateada = ""

    cargo_banco = fields.Char(compute="_compute_pagos")
    num_cheque_asociado = fields.Char(compute="_compute_pagos")
    tiene_efectivo = fields.Boolean(compute="_compute_pagos")
    tiene_cheque = fields.Boolean(compute="_compute_pagos")
    tiene_transferencia = fields.Boolean(compute="_compute_pagos")
    tiene_retenciones = fields.Boolean(compute="_compute_pagos")

    @api.depends("tiene_efectivo", "tiene_cheque", "tiene_transferencia", "num_cheque_asociado", "payment_ids")
    def _compute_pagos(self):
        for record in self:
            record.tiene_efectivo = False
            record.tiene_cheque = False
            record.tiene_transferencia = False
            record.tiene_retenciones = False
            record.num_cheque_asociado = False
            record.cargo_banco = False
            for pago in record.payment_ids:
                if not record.cargo_banco:
                    record.cargo_banco = pago.journal_id.name
                if pago.journal_id.type == "cash" and not pago.numero_cheque_recibo:
                    record.tiene_efectivo = True
                if pago.journal_id.payment_subtype:
                    record.tiene_cheque = True

                    if not record.num_cheque_asociado:
                        record.num_cheque_asociado = pago.numero_cheque_recibo

                if pago.journal_id.type == "bank" and not pago.journal_id.payment_subtype:
                    if not pago.numero_cheque_recibo:
                        record.tiene_transferencia = True
                if int(pago.journal_id.tipo_pago) == 10:
                    record.tiene_retenciones = True

    def monto_simbolo(self, numero, largo_contenedor_cm=5.35, ancho_por_caracter_cm=0.2):
        # se agrega condicion para el formato del numero al imprimir los recibos
        if 'USD' in self.currency_invoice.name:
            texto = str(numero)  #se mantiene en float si es USD
        else:
            numero = str(numero).replace('.', '').replace(',', '.') #se convierte en integer si es moneda distinta
            texto = f"{int(float(numero)):,}".replace(',', '.')

        # Calculamos el largo del texto en cm
        largo_texto_cm = len(texto) * ancho_por_caracter_cm
        if largo_texto_cm >= largo_contenedor_cm:
            # Recortamos el texto para que encaje exactamente en el contenedor
            max_caracteres = int(largo_contenedor_cm / ancho_por_caracter_cm)
            texto = texto[:max_caracteres]
            return texto  # Sin guiones porque ya está lleno

        # Calculamos el espacio restante en cm
        espacio_restante_cm = largo_contenedor_cm - largo_texto_cm

        # Calculamos cuántos guiones caben en el espacio restante
        guiones_faltantes = int(espacio_restante_cm / ancho_por_caracter_cm)
        guiones = '-' * guiones_faltantes

        # Concatenamos el texto con los guiones
        texto_ajustado = texto + '  ' + guiones

        return texto_ajustado

    def calcular_letras(self, numero):
        entero = int(numero)
        letras = num2words(entero, lang='es').upper()
        letras = 'GUARANIES ' + letras
        # letras = letras + '.-'
        return letras

    # def calcular_letras(self, numero):
    #     letras = self.monto_en_letras = num2words(numero, lang='es').upper()
    #     letras = '--' + 'GUARANIES ' + letras + '--'
    #     return letras

    def calcular_letras_dolar(self, numero):
        nuevo_numero = str(numero).split('.')
        entero = num2words(int(nuevo_numero[0]), lang='es').upper()
        # if len(nuevo_numero[1] == 1):
        if len(nuevo_numero[1]) == 1:
            if nuevo_numero[1] == '0':
                decimal = num2words(int(nuevo_numero[1]), lang='es').upper()
            else:
                decimal = num2words(int(nuevo_numero[1] + '0'), lang='es').upper()
        else:
            decimal = num2words(int(nuevo_numero[1]), lang='es').upper()
        letras = entero + ' DOLARES ' + ' CON ' + decimal + ' CENTAVOS '
        return letras

    def conversion_monetaria_fact(self, numero, moneda):
        entero = int(numero)
        if ('EUR' in moneda) or ('USD' in moneda):
            decimal = str(numero)
            numero_con_punto = ''
            print(f"decimal ->{decimal}")
            entero_string = '.'.join([str(int(entero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                            ::-1]
            print(f"entero_string->{entero_string}")
            decimal_string = str(decimal).split('.')
            print(f"decimal_string->{decimal_string}")
            if decimal_string and len(decimal_string) > 1:
                if decimal_string and len(decimal_string[1]) >= 2:
                    numero_con_punto = entero_string + ',' + decimal_string[1][:2]
                elif len(decimal_string[1]) < 2 and decimal_string[1] != '00':
                    numero_con_punto = entero_string + ',' + decimal_string[1] + '0'
                elif len(decimal_string[1]) < 2 and decimal_string[1] == '0':
                    numero_con_punto = entero_string + ',' + decimal_string[1]
            else:
                print("ENtra en el else")
                numero_con_punto = entero_string
        else:
            numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                               ::-1]

        num_return = numero_con_punto
        print(numero_con_punto)
        return num_return

    def agregar_punto_de_miles(self, numero, moneda):
        entero = int(numero)
        if 'USD' in moneda:

            decimal = '{0:.2f}'.format(numero - entero)
            entero_string = '.'.join([str(int(entero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                            ::-1]
            if decimal == '0.00':
                numero_con_punto = 'USD' + ' ' + entero_string + ',00'
            else:
                decimal_string = str(decimal).split('.')
                numero_con_punto = 'USD' + ' ' + entero_string + ',' + decimal_string[1]
        elif 'PYG' in moneda:
            numero_con_punto = 'GS' + '.'.join(
                [str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(numero))), 3)])[
                                      ::-1]
            return numero_con_punto
        else:
            numero_con_punto = '.'.join([str(int(numero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                               ::-1]
        num_return = ' ' + numero_con_punto
        return num_return

    def monto_cobros_en_lineas(self, moneda):
        """"
           Retorna las lineas dependiendo del la cantidad de caracteres del monto,
           ajustado solo para el recibo comun, con la fuente y tamanio de letra actual
            font-family: Arial, sans-serif; font-size: 18px;
        """
        multi_linea = False
        linea1 = False

        linea2 = False
        if moneda == 'PYG':
            monto_letras = self.calcular_letras(self.total_cobros)

        else:
            monto_letras = self.calcular_letras_dolar(self.total_cobros)

        # para caso de una sola linea
        concepto = self.concepto if self.concepto else ""
        if len(monto_letras) < 68 or len(concepto) < 68:
            linea1 = monto_letras
        if len(monto_letras) > 68:
            linea1 = monto_letras[0:68]
            linea2 = monto_letras[68:len(monto_letras)]
            multi_linea = True
        else:
            linea1 = monto_letras

        return multi_linea, linea1, linea2


    # def monto_concepto(self, concepto, limite=68):
    #     if not concepto:
    #         return False, "", ""  # Si no hay concepto, devolver valores vacíos
    #
    #     concepto = concepto.strip()  # Elimina espacios en blanco extra
    #
    #     # Caso de una sola línea
    #     if len(concepto) <= limite:
    #         linea1 = concepto.ljust(limite, '-')  # Completa con guiones hasta el límite
    #         return False, linea1, ""
    #
    #     # Caso de varias líneas
    #     linea1 = concepto[:limite]  # Primera línea de hasta 'limite' caracteres
    #     linea2 = concepto[limite:]  # Segunda línea con el resto del texto
    #
    #     return True, linea1, linea2
