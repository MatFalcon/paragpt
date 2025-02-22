# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from odoo import models, fields, api
from itertools import groupby


class WizardReportePresupuestos(models.TransientModel):
    _name = 'wizard_reporte_presupuestos'
    _description = 'Wizard Reporte de Presupuestos'

    crossovered_budget_id = fields.Many2one('crossovered.budget', string="Presupuesto")

    def print_report_xlsx(self):
        data = {
            'crossovered_budget_id': self.crossovered_budget_id.id
        }
        return self.env.ref('situaciones_presupuestarias.report_action_presupuestos').report_action(self, data=data)


class ReportePresupuestos(models.AbstractModel):
    _name = 'report.situaciones_presupuestarias.reporte_presupuestos_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def get_first_date_of_month(self, year, month):
        first_date = datetime(year, month, 1)
        return first_date.date()

    def get_last_date_of_month(self, year, month):
        if month == 12:
            last_date = datetime(year, month, 31)
        else:
            last_date = datetime(year, month + 1, 1) + timedelta(days=-1)
        return last_date.date()

    def generate_xlsx_report(self, workbook, data, datas):

        global sheet
        global bold
        global num_format
        global position_x
        global position_y
        sheet = workbook.add_worksheet('Presupuestado')
        bold = workbook.add_format({'bold': True, 'font_name': 'Roboto'})
        subtitulo = workbook.add_format(
            {'color': '#ffffff', 'bold': True, 'bg_color': '#501e53', 'font_name': 'Roboto'})
        titulo = workbook.add_format({'color': '#000000', 'bold': True, 'bg_color': '#f2f2f2', 'font_name': 'Roboto'})
        subtitulo2 = workbook.add_format(
            {'color': '#000000', 'bold': True, 'bg_color': '#b0b0b0', 'font_name': 'Roboto'})
        numerico = workbook.add_format({'num_format': True, 'align': 'right', 'font_name': 'Roboto'})
        numerico.set_num_format('#,##0')
        numerico_total = workbook.add_format(
            {'num_format': True, 'align': 'right', 'bold': True, 'font_name': 'Roboto'})

        numerico_total.set_num_format('#,##0')
        numerico_titulo = workbook.add_format({'color': '#000000', 'bold': True, 'bg_color': '#f2f2f2',
                                               'font_name': 'Roboto', 'num_format': True, 'align': 'right'})
        numerico_titulo.set_num_format('#,##0')
        numerico_subtitulo2 = workbook.add_format({'color': '#000000', 'bold': True, 'bg_color': '#b0b0b0',
                                                   'font_name': 'Roboto', 'num_format': '#,##0',
                                                   'align': 'right'})
        wrapped_text = workbook.add_format()
        wrapped_text.set_text_wrap()
        wrapped_text_bold = workbook.add_format({'bold': True})
        wrapped_text_bold.set_text_wrap()

        position_x = 0
        position_y = 0

        budget = self.env['crossovered.budget'].browse(data['crossovered_budget_id'])

        def resetPositions():
            global position_y
            global position_x
            position_y = 0
            position_x = position_x + 3

        def addSalto(pos_inicio=None):
            global position_x
            global position_y
            position_x = pos_inicio
            position_y += 1

        def addRight():
            global position_x
            position_x += 1

        def breakAndWrite(to_write, format=None):
            global sheet
            addSalto()
            sheet.write(position_y, position_x, to_write, format)

        def simpleWrite(to_write, format=None):
            global sheet
            sheet.write(position_y, position_x, to_write, format)

        def rightAndWrite(to_write, format=None):
            global sheet
            addRight()
            sheet.write(position_y, position_x, to_write, format)

        def printSumas(comp=None, campo=None, padre = None):
            lineas_grupo = budget.mapped('crossovered_budget_line').filtered(
                lambda x: x.general_budget_id.account_ids.group_id in comp)

            fechas = set(lineas_grupo.mapped('date_from'))

            fechas = sorted(list(fechas))

            suma_por_fecha = []
            if campo == 'percentage':
                planned = sum(lineas_grupo.mapped('planned_amount'))
                practical = sum(lineas_grupo.mapped('practical_amount'))
                if planned:
                    percentage = round(practical * 100 / planned,1)
                else:
                    percentage = 0
                monto_total_linea = percentage
            else:
                monto_total_linea = sum(lineas_grupo.mapped(campo))

            for fecha in fechas:
                if campo == 'percentage':
                    planned = sum(lineas_grupo.filtered(lambda x: x.date_from == fecha).mapped('planned_amount'))
                    practical = sum(lineas_grupo.filtered(lambda x: x.date_from == fecha).mapped('practical_amount'))
                    if planned:
                        percentage = round(practical * 100 / planned,1)
                    else:
                        percentage = 0
                    suma_por_fecha.append({'fecha': fecha, 'monto': str(percentage)+ '%'})
                else:
                    monto = sum(lineas_grupo.filtered(lambda x: x.date_from == fecha).mapped(campo))
                    suma_por_fecha.append({'fecha': fecha, 'monto': monto})

            for i in suma_por_fecha:
                rightAndWrite(i['monto'], numerico_subtitulo2)

            if campo != 'percentage':
                rightAndWrite(monto_total_linea, numerico_subtitulo2)
            else:
                rightAndWrite(str(monto_total_linea) + '%', numerico_subtitulo2)
            if not padre:
                return fechas
            else:
                return suma_por_fecha

        def imprimirTitulos():
            rightAndWrite('Enero', subtitulo)
            rightAndWrite('Febrero', subtitulo)
            rightAndWrite('Marzo', subtitulo)
            rightAndWrite('Abril', subtitulo)
            rightAndWrite('Mayo', subtitulo)
            rightAndWrite('Junio', subtitulo)
            rightAndWrite('Julio', subtitulo)
            rightAndWrite('Agosto', subtitulo)
            rightAndWrite('Septiembre', subtitulo)
            rightAndWrite('Octubre', subtitulo)
            rightAndWrite('Noviembre', subtitulo)
            rightAndWrite('Diciembre', subtitulo)
            rightAndWrite('Total', subtitulo)

        def imprimirLineas(campo, pos_inicio):
            ingresos = []
            egresos = []
            diferencia = []
            if budget:
                # Obtenemos las cuentas y los grupos (ordenados por codigo) presentes en las lineas de presupesto.
                cuentas = set(budget.mapped('crossovered_budget_line.general_budget_id.account_ids.id'))
                cuentas = self.env['account.account'].search([('id', 'in', list(cuentas))], order='code asc')
                grupos = list(set(cuentas.mapped('group_id.id')))
                grupos = self.env['account.group'].search([('id', 'in', grupos)], order='code_prefix_start asc')

                # Crear un diccionario para almacenar grupos padres y sus hijos
                diccionario_grupos = {}

                # Iterar sobre los grupos hijos y organizarlos por grupos padres
                for grupo_hijo in grupos:
                    # Obtener el primer dígito del código del grupo hijo
                    primer_digito_hijo = int(str(grupo_hijo.code_prefix_start)[0])

                    # Buscar el grupo padre según la condición
                    grupo_padre = self.env['account.group'].search([('code_prefix_start', '=', primer_digito_hijo)],
                                                                   limit=1)
                    # Agregar el grupo hijo al diccionario bajo el grupo padre correspondiente
                    if grupo_padre:
                        diccionario_grupos.setdefault(grupo_padre, []).append(grupo_hijo)

                for grupo_padre, lista_hijos in diccionario_grupos.items():
                    addSalto(pos_inicio=pos_inicio)
                    simpleWrite(grupo_padre.code_prefix_start, subtitulo2)
                    rightAndWrite(grupo_padre.name, subtitulo2)

                    hijos = []
                    for lh in lista_hijos:
                        hijos.append(lh)
                    suma_por_fecha = printSumas(hijos, campo, padre = True)
                    if grupo_padre.code_prefix_start[0] == '4':
                        ingresos = suma_por_fecha
                    elif grupo_padre.code_prefix_start[0] == '5':
                        egresos = suma_por_fecha
                    mes = 0
                    if len(ingresos) > 0 and len(egresos)>0 and campo != 'percentage':
                        while mes < 12:
                            monto = ingresos[mes]['monto']-egresos[mes]['monto']
                            diferencia.append({'fecha':ingresos[mes]['fecha'],'monto':monto})
                            mes = mes + 1
                    for g in lista_hijos:
                        addSalto(pos_inicio=pos_inicio)
                        simpleWrite(g.code_prefix_start, subtitulo2)
                        rightAndWrite(g.name, subtitulo2)
                        cuentas_grupo = cuentas.filtered(lambda x: x.group_id == g)
                        fechas = printSumas(g, campo, padre=False)

                        for c in cuentas_grupo:
                            lineas_budget = budget.mapped('crossovered_budget_line').filtered(
                                lambda x: x.general_budget_id.account_ids == c)
                            if lineas_budget:
                                addSalto(pos_inicio=pos_inicio)
                                simpleWrite(c.code, titulo)
                                rightAndWrite(c.name, titulo)
                                for fecha in fechas:
                                    monto = sum(lineas_budget.filtered(lambda x: x.date_from == fecha).mapped(campo))
                                    if campo == 'percentage':
                                        rightAndWrite(str(round(monto,1)) + '%', numerico_titulo)
                                    else:
                                        rightAndWrite(monto, numerico_titulo)
                                if campo == 'percentage':
                                    rightAndWrite(str(round(sum(lineas_budget.mapped(campo)),1)) + '%', numerico_total)
                                else:
                                    rightAndWrite(sum(lineas_budget.mapped(campo)), numerico_total)
                                cuentas_analiticas = list(set(lineas_budget.mapped('analytic_account_id')))
                                for ca in cuentas_analiticas:
                                    addSalto(pos_inicio=pos_inicio)
                                    simpleWrite(c.code)
                                    rightAndWrite(ca.name)
                                    suma_cuenta = 0
                                    for l in lineas_budget.filtered(lambda x: x.analytic_account_id == ca):
                                        if campo == 'planned_amount':
                                            rightAndWrite(l.planned_amount, numerico)
                                            suma_cuenta = suma_cuenta + l.planned_amount
                                        elif campo == 'practical_amount':
                                            rightAndWrite(l.practical_amount, numerico)
                                            suma_cuenta = suma_cuenta + l.practical_amount
                                        elif campo == 'percentage':
                                            rightAndWrite(str(round(l.percentage,1))+'%', numerico)
                                            suma_cuenta = suma_cuenta + l.percentage
                                    if campo == 'percentage':
                                        rightAndWrite(str(round(suma_cuenta,1))+ '%', numerico)
                                    else:
                                        rightAndWrite(suma_cuenta, numerico)

                    if len(diferencia) > 0:
                        addSalto(pos_inicio=pos_inicio)
                        rightAndWrite('RESULTADOS',subtitulo2)
                        x = 0
                        diferencia_total = 0
                        while x<12:
                            rightAndWrite(diferencia[x]['monto'], numerico_subtitulo2)
                            diferencia_total = diferencia_total + diferencia[x]['monto']
                            x =x+1
                        rightAndWrite(diferencia_total, numerico_subtitulo2)
                        addSalto(pos_inicio=pos_inicio)
                        rightAndWrite('RESULTADOS ACUMULADOS', subtitulo2)
                        x = 0
                        diferencia_total = 0
                        while x < 12:
                            diferencia_total = diferencia_total + diferencia[x]['monto']
                            rightAndWrite(diferencia_total, numerico_subtitulo2)
                            x = x + 1
                        rightAndWrite(diferencia_total, numerico_subtitulo2)


        """def printAll(name, campo):
            if pos_inicio != 0:
                resetPositions()
            global position_y
            simpleWrite(name, titulo)
            position_y = position_y + 1
            simpleWrite('Cuenta', subtitulo)
            rightAndWrite('Descripción', subtitulo)
            imprimirTitulos()

        printAll('PRESUPUESTADO')
        imprimirLineas('planned_amount', pos_inicio=0)

        printAll('EJECUTADO')
        pos_inicio = position_x
        imprimirLineas('practical_amount', pos_inicio=pos_inicio)

        printAll('LOGRADO')
        pos_inicio = position_x
        imprimirLineas('percentage', pos_inicio=pos_inicio)
        
        printAll('VARIACION', 'difference_amount')
        pos_inicio = position_x
        imprimirLineas('difference_amount', pos_inicio=pos_inicio)"""

        simpleWrite('PRESUPUESTADO', titulo)
        position_y = position_y + 1
        simpleWrite('Cuenta', subtitulo)
        rightAndWrite('Descripción', subtitulo)
        imprimirTitulos()
        imprimirLineas('planned_amount', pos_inicio=0)


        resetPositions()
        simpleWrite('EJECUTADO', titulo)
        position_y = position_y + 1
        pos_inicio = position_x
        simpleWrite('Cuenta', subtitulo)
        rightAndWrite('Descripción', subtitulo)
        imprimirTitulos()
        imprimirLineas('practical_amount', pos_inicio=pos_inicio)

        resetPositions()
        simpleWrite('LOGRADO', titulo)
        position_y = position_y + 1
        pos_inicio = position_x
        simpleWrite('Cuenta', subtitulo)
        rightAndWrite('Descripción', subtitulo)
        imprimirTitulos()
        imprimirLineas('percentage', pos_inicio=pos_inicio)

        resetPositions()
        simpleWrite('VARIACION', titulo)
        position_y = position_y + 1
        pos_inicio = position_x
        simpleWrite('Cuenta', subtitulo)
        rightAndWrite('Descripción', subtitulo)
        imprimirTitulos()
        imprimirLineas('difference_amount', pos_inicio=pos_inicio)