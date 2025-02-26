# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions, api
import re


class HrContract(models.Model):
    _inherit = 'hr.contract'

    dia_contrato = fields.Char('Dia Contrato', compute="_computeDiaMesAnhoContrato")
    mes_contrato = fields.Char('Mes Contrato', compute="_computeDiaMesAnhoContrato")
    anho_contrato = fields.Char('Año Contrato', compute="_computeDiaMesAnhoContrato")
    plantilla_id = fields.Many2one('plantilla.contrato', string="Plantilla de Contrato")
    contenido = fields.Text(string='Contenido', compute="_computeContenido")
    fecha_inicio_contrato = fields.Char(compute='_get_fecha_inicio_fin_contrato')
    fecha_fin_contrato = fields.Char(compute='_get_fecha_inicio_fin_contrato')

    contacto_accidente = fields.Many2one('res.partner', string="Contacto en caso de accidente")
    funciones_a_realizar_lugar_trabajo = fields.Char(string="Funciones a Realizar en el lugar de trabajo")
    nombre_lugar_trabajo = fields.Char(string="Nombre lugar de trabajo")
    ciudad_lugar_trabajo = fields.Char(string="Ciudad lugar de trabajo")
    distrito_lugar_trabajo = fields.Char(string="Distrito lugar de trabajo")
    state_id_lugar_trabajo = fields.Many2one('res.country.state', string='Departamento lugar de trabajo')
    # construccion_casa = fields.Selection(selection=[('madera', 'Madera'), ('material', 'Material')],
    #                                      string="Tipo de Construccion de la casa", default="madera")
    # responsable_horas_extra_id = fields.Many2one('hr.employee', string="Responsable de horas extra")
    dia_descanso = fields.Selection(
        selection=[('lunes', 'Lunes'), ('martes', 'Martes'), ('martes', 'Martes'), ('miercoles', 'Miercoles'),
                   ('jueves', 'Jueves'), ('viernes', 'Viernes'), ('sabado', 'Sabado'), ('domingo', 'Domingo')],
        string="Dia de descanso", default="domingo")
    # tiempo_lugar_ensenanza = fields.Char(string="Tiempo y Lugar de enseñanza")

    duracion_jornada_trabajo = fields.Text(string='Duración y días de la jornada de trabajo')

    def _get_fecha_inicio_fin_contrato(self):
        for this in self:
            this.fecha_inicio_contrato = this.date_start.strftime('%d-%m-%Y')
            if this.date_end:
                this.fecha_fin_contrato = this.date_end.strftime('%d-%m-%Y') + '. El contrato es con tiempo definido'
            else:
                this.fecha_fin_contrato = 'Indefinido'

    def _computeDiaMesAnhoContrato(self):
        for this in self:
            this.dia_contrato = this.date_start.day
            meses = {
                1: 'Enero',
                2: 'Febrero',
                3: 'Marzo',
                4: 'Abril',
                5: 'Mayo',
                6: 'Junio',
                7: 'Julio',
                8: 'Agosto',
                9: 'Setiembre',
                10: 'Octubre',
                11: 'Noviembre',
                12: 'Diciembre',
            }
            this.mes_contrato = meses.get(this.date_start.month)
            this.anho_contrato = this.date_start.year

    @api.onchange('plantilla_id')
    def _computeContenido(self):
        for this in self:
            contenido = '<div>'
            if this.plantilla_id:
                if this.plantilla_id.seccion_ids:
                    secciones = sorted(this.plantilla_id.seccion_ids, key=lambda x: x['secuencia'])
                    for seccion in secciones:
                        if seccion.tipo == 'titulo_nueva_pagina':
                            contenido += '<div style="page-break-after:always;"></div>'

                            contenido = contenido + "<h2 style='text-align:center;'>" + seccion.texto + "</h2>"
                        else:
                            contenido = contenido + "<br></br>" + seccion.texto
                            items = seccion.items_ids.sorted(key=lambda y: y['secuencia'])
                            for padre in items.filtered(lambda z: not z.parent_id):
                                contenido = contenido + "<br></br>" + padre.texto
                                for hijo in items.filtered(lambda z: z.parent_id == padre):
                                    contenido = contenido + "<br></br>" + hijo.texto
                                    for hijo_2 in items.filtered(lambda z: z.parent_id == hijo):
                                        contenido = contenido + "<br></br>" + hijo_2.texto

                            contenido = contenido + '<br></br>'
                            if seccion.tipo == 'pie':
                                contenido += '''
                                            <div class="row">
                                                <table style="width:100%;margin-top:100px;text-align:center;">
                                                    <tr>
                                                        <td  style="border-bottom:1px solid black;"/>
                                                        <td style='width:15%;'></td>
                                                        <td  style="border-bottom:1px solid black;"/>
                                                    </tr>
                                                    <tr>
                                                        <td>
                                                            ''' + \
                                             this.company_id.name + ' ' + \
                                             '''
                                                        </td>
                                                        <td style='width:15%;'></td>
                                                        <td>
                                                            ''' + (this.employee_id.name or '') + '''
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <td>
                                                        C.I. N° ''' + (this.company_id.vat_no_verification_digit or '') + '''
                                                        </td>
                                                        <td style='width:15%;'></td>
                                                        <td>
                                                        C.I. N° ''' + (this.employee_id.identification_id or '') + '''
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                    <td>''' + this.company_id.representante_legal_pronouns_el_la_empleador_ra + '''</td>
                                                        <td style='width:15%;'></td>
                                                    <td>''' + this.employee_id.pronouns_el_la_empleado_a + '''</td>
                                                    </tr>
                                                </table>
                                            </div>
                                '''
            contenido = contenido + '</div>'

            def buscar_y_reemplazar_patron(this, patron_re, contenido, tipo_patron):
                matches = re.finditer(patron_re, contenido)
                for i in matches:
                    if tipo_patron == 'variable':
                        var = i.group(1)
                        var = var.replace('__', '.')
                        variable = 'this.' + var
                        variable_value = eval(variable)
                        if not variable_value:
                            variable_value = '<span style="color: red;">definir variable ' + var + '</span>'
                        variable_value = str(variable_value)
                        contenido = contenido.replace(i.group(0), variable_value)
                    if tipo_patron == 'negrita':
                        var = i.group(1)
                        variable_value = str('<b>' + var + '</b>')
                        contenido = contenido.replace(i.group(0), variable_value)

                return contenido

            contenido = buscar_y_reemplazar_patron(this=this, patron_re='<<(\w*)>>', contenido=contenido, tipo_patron='variable')
            contenido = buscar_y_reemplazar_patron(this=this, patron_re='<b<([^>]*)>b>', contenido=contenido, tipo_patron='negrita')
            this.contenido = contenido
