from odoo import models, fields, api

class recibo_cobranza(models.Model):
    _inherit = 'account.recibo'

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

    def conversion_monetaria_fact(self, numero, moneda):
        # Eliminar espacios en blanco y separadores de miles
        numero = numero.replace('.', '').strip()

        # Convertir a entero de forma segura
        entero = int(numero)

        if ('EUR' in moneda) or ('USD' in moneda):
            decimal = str(numero)
            numero_con_punto = ''

            entero_string = '.'.join([str(int(entero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                            ::-1]

            decimal_string = decimal.split('.')

            if decimal_string and len(decimal_string) > 1:
                if decimal_string and len(decimal_string[1]) >= 2:
                    numero_con_punto = entero_string + ',' + decimal_string[1][:2]
                elif len(decimal_string[1]) < 2 and decimal_string[1] != '00':
                    numero_con_punto = entero_string + ',' + decimal_string[1] + '0'
                elif len(decimal_string[1]) < 2 and decimal_string[1] == '0':
                    numero_con_punto = entero_string + ',' + decimal_string[1]
            else:
                numero_con_punto = entero_string
        else:
            numero_con_punto = '.'.join([str(int(entero))[::-1][i:i + 3] for i in range(0, len(str(int(entero))), 3)])[
                               ::-1]

        return numero_con_punto

    def monto_cobros_en_lineas(self, moneda):
        multi_linea = False
        linea1 = False
        linea2 = False

        if not self.concepto:
            return multi_linea, "", ""

        concepto_texto = self.concepto.strip()

        # Caso de una sola línea
        if len(concepto_texto) <= 68:
            linea1 = concepto_texto
        else:
            linea1 = concepto_texto[:68].strip()
            linea2 = concepto_texto[68:].strip()
            multi_linea = True

        return multi_linea, linea1, linea2




