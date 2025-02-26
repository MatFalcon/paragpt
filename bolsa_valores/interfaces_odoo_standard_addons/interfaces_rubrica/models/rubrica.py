# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, release

import PyPDF2
import os
import tempfile
import base64
from fpdf import FPDF
from werkzeug.urls import url_encode, url_join
from odoo.tools.misc import format_date, DEFAULT_SERVER_DATE_FORMAT
import logging

_logger = logging.getLogger(__name__)

characters_to_replace = ['\u200b', '\u201c']


def format_number_to_string(number):
    if number == '':
        return ''
    return '{0:,.0f}'.format(int(number)).replace(',', '.')


def clean_string(string):
    allowed_characters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,1234567890!@#$%^&*()'
    return string


class RegistroRubricas(models.Model):
    _name = 'interfaces_rubrica.registro_rubrica'
    _description = 'interfaces_rubrica.registro_rubrica'

    name = fields.Char(string="Name")
    nro_ini = fields.Integer(string="Nro. Inicial")
    nro_fin = fields.Integer(string="Nro. Final")
    nro_actual = fields.Integer(string="Ultimo Nro.")
    imagen = fields.Binary(string="Imagen de Rúbrica")
    company_id = fields.Many2one('res.company', string="Empresa")
    activo = fields.Boolean(string="Registro Activo")
    type = fields.Selection(string="Tipo", selection=[
        ('compra', 'Libro de Compra'),
        ('venta', 'Libro de Venta'),
        ('diario', 'Libro Diario'),
        ('mayor', 'Libro Mayor'),
        ('inventario', 'Libro Inventario')
    ])


class InformesRubricas(models.Model):
    _name = 'interfaces_rubrica.informe_rubrica'
    _description = 'interfaces_rubrica.informe_rubrica'

    name = fields.Char(string="Nombre")
    page_qty = fields.Integer(string="Cantidad de Páginas")
    rubrica_id = fields.Many2one('interfaces_rubrica.registro_rubrica', string="Rúbrica",
                                 domain="[('activo','=', True),('company_id','=',company_id)]")
    archivo_rub = fields.Binary(string="Archivo")
    archivo_nombre = fields.Char(string="Nombre de Archivo")
    company_id = fields.Many2one("res.company", string="Compañía", default=lambda self: self.env.company)
    activo = fields.Boolean(string="Registro Activo")
    detallado = fields.Boolean(string="Informe Detallado")
    type = fields.Selection(string="Tipo", selection=[
        ('compra', 'Libro de Compra'),
        ('venta', 'Libro de Venta'),
        ('diario', 'Libro Diario'),
        ('diario_resumido_mensual', 'Libro Diario resumido - por mes'),
        ('diario_resumido_dia', 'Libro Diario resumido - por día'),
        ('mayor', 'Libro Mayor'),
        ('inventario', 'Libro Inventario')
    ])
    state = fields.Selection(string="Estado", selection=[
        ('draft', 'Borrador'),
        ('printed', 'Impreso'),
        ('cancel', 'Cancelado'),
    ], default='draft')
    nro_rub_act = fields.Integer(string="Nro. Actual")
    nro_rub_ini = fields.Integer(string="Nro. Inicio")
    nro_rub_fin = fields.Integer(string="Nro. Final")
    fecha_inicio = fields.Date(string="Fecha Inicio")
    fecha_fin = fields.Date(string="Fecha Fin")

    @api.onchange('rubrica_id')
    @api.depends('rubrica_id')
    def test_onchange(self):
        for record in self:
            record.nro_rub_act = self.rubrica_id.nro_actual
            record.nro_rub_ini = self.rubrica_id.nro_ini
            record.nro_rub_fin = self.rubrica_id.nro_fin

    @api.model
    def create(self, vals):
        res = super(InformesRubricas, self).create(vals)
        res.name = "{0} - {1}".format(res.type, fields.Date.today())
        return res

    def descargar_pdf(self):

        if not self.archivo_rub:
            raise exceptions.UserError("Favor generar el archivo antes de imprimir")

        if self.nro_rub_fin < self.nro_rub_act + self.page_qty:
            raise exceptions.UserError("La cantidad de páginas excede el nro máximo disponible")

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        download_url = url_join(base_url, '/binary/download')

        params = {
            'record_id': self.id,
        }
        query_string = url_encode(params)

        complete_url = "{}?{}".format(download_url, query_string)

        self.state = 'printed'
        self.rubrica_id.nro_actual += self.page_qty
        # 'url': '/binary/download/?request_id={0}'.format(self.id),
        return {
            'type': 'ir.actions.act_url',
            'url': complete_url,
            'target': 'new',
        }

    def cancelar_rubrica(self):
        nro_actual = self.rubrica_id.nro_actual
        if nro_actual != self.nro_rub_act + self.page_qty:
            raise exceptions.UserError("No se puede cancelar el documento, no corresponde al la última secuencia")

        self.rubrica_id.nro_actual -= self.page_qty
        self.state = 'cancel'

    def reset_formulario(self):
        # if self.
        self.archivo_rub = False
        self.state = 'draft'

    def generar_pdf(self):
        if self.type == 'diario':
            # try:
            self.libro_diario_pdf()
            # except:
            #    raise exceptions.UserError("Error al generar pdf")

        if self.type == 'diario_resumido_mensual':
            try:
                self.libro_diario_resumido_mensual_pdf()
            except Exception as ex:
                _logger.error(ex)
                raise exceptions.UserError("Error al generar pdf")

        if self.type == 'diario_resumido_dia':
            try:
                self.libro_diario_resumido_dia_pdf()
            except Exception as ex:
                _logger.error(ex)
                raise exceptions.UserError("Error al generar pdf")

        if self.type == 'mayor':
            #self.libro_mayor_pdf()
            try:
                self.libro_mayor_pdf()
            except:
                raise exceptions.UserError("Error al generar pdf")

        if self.type == 'compra':
            # self.libro_compra_venta_pdf(tipo='compra')

            try:
                self.libro_compra_venta_pdf(tipo='compra')
            except:
                raise exceptions.UserError("Error al generar pdf")
            self.libro_compra_venta_pdf(tipo='compra')
        if self.type == 'venta':
            try:
                self.libro_compra_venta_pdf(tipo='venta')
            except:
                raise exceptions.UserError("Error al generar pdf")

        if self.type == 'inventario':
            self.libro_inventario_pdf()
            # try:
            #     self.libro_inventario_pdf()
            # except:
            #     raise exceptions.UserError("Error al generar pdf")

    def libro_compra_venta_pdf(self, tipo=None):
        facturas = []
        if tipo == 'compra':
            facturas = self.env['account.move'].search([
                ('move_type', '=', 'in_invoice'),
                ('state', 'in', ['posted']),
                ('invoice_date', '>=', self.fecha_inicio),
                ('invoice_date', '<=', self.fecha_fin),
                ('line_ids.tax_ids', '!=', False),
                ('company_id', '=', self.company_id.id)
            ])
            TABLE_DATA_FACTURAS = [(
                'Nro',
                'Fecha',
                'Proveedor',
                'RUC',
                'Tipo doc',
                'Timbrado',
                'Nro Doc',
                "Gravadas 10%",  # "Importe Gravadas 10%",
                "IVA 10%",  # "Debito fiscal 10%",
                "Gravadas 5%",  # "Importe Gravadas 5%",
                "IVA 5%",  # "Debito fiscal 5%",
                "Exentas",  # "Importes Exentas",
                "Total"  # "Importe total facturado con IVA incluido",
            )]

        if tipo == 'venta':
            facturas = self.env['account.move'].search([
                ('move_type', '=', 'out_invoice'),
                ('state', 'in', ['posted', 'cancel']),
                ('invoice_date', '>=', self.fecha_inicio),
                ('invoice_date', '<=', self.fecha_fin),
                ('company_id', '=', self.company_id.id)
            ])

            TABLE_DATA_FACTURAS = [(
                'Nro',
                'Fecha',
                'Cliente',
                'RUC',
                'Tipo doc',
                'Nro Doc',
                "Gravadas 10%",  # "Importe Gravadas 10%",
                "IVA 10%",  # "Debito fiscal 10%",
                "Gravadas 5%",  # "Importe Gravadas 5%",
                "IVA 5%",  # "Debito fiscal 5%",
                "Exentas",  # "Importes Exentas",
                "Total"  # "Importe total facturado con IVA incluido",
            )]

        pdf = CustomPDF()
        pdf.start_page_number = self.rubrica_id.nro_actual
        pdf.company = self.company_id
        titulo = """
        Libro {0} - Ley 125/91 Periodo: Del {1} al {2}
        """.format(tipo, self.fecha_inicio.strftime('%d/%m/%Y'), self.fecha_fin.strftime('%d/%m/%Y'))
        pdf.titulo_enc = titulo
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)

        pdf.set_font("Arial", "B", 10)
        pdf.add_page()
        # pdf.cell(0, 2, "".format(), align="L", ln=True)
        # pdf.cell(0, 6, "Libro de {0} - Ley 125/91".format(tipo), align="L", ln=True)
        pdf.cell(0, 6, "", align="L", ln=True)

        cont = 0
        total_gral_total = 0
        total_gral_base10 = 0
        total_gral_base5 = 0
        total_gral_iva10 = 0
        total_gral_iva5 = 0
        total_gral_exentas = 0
        for i in facturas.sorted(key=lambda r: r.invoice_date):
            a = 1
            cont += 1
            total_factura = 0
            if i.state != 'cancel':
                total_factura = abs(i.amount_total_signed)
            base10 = 0
            base5 = 0
            exentas = 0
            iva10 = 0
            iva5 = 0

            for t in i.filtered(lambda x: x.state != 'cancel').invoice_line_ids:
                if t.tax_ids and t.tax_ids[0].amount == 10:
                    base10 += t.price_total / 1.1
                    iva10 += t.price_total / 11
                if t.tax_ids and t.tax_ids[0].amount == 5:
                    base5 += t.price_total / 1.05
                    iva5 += t.price_total / 21
                if (t.tax_ids and t.tax_ids[0].amount == 0) or not t.tax_ids:
                    exentas += t.price_total

            if i.currency_id != self.company_id.currency_id:
                base10 = i.currency_id._convert(
                    base10, self.company_id.currency_id, self.company_id, i.invoice_date)
                iva10 = i.currency_id._convert(
                    iva10, self.company_id.currency_id, self.company_id, i.invoice_date)
                base5 = i.currency_id._convert(
                    base5, self.company_id.currency_id, self.company_id, i.invoice_date)
                iva5 = i.currency_id._convert(
                    iva5, self.company_id.currency_id, self.company_id, i.invoice_date)
                exentas = i.currency_id._convert(
                    exentas, self.company_id.currency_id, self.company_id, i.invoice_date)

            total_gral_total += total_factura
            total_gral_base10 += base10
            total_gral_base5 += base5
            total_gral_iva10 += iva10
            total_gral_iva5 += iva5
            total_gral_exentas += exentas

            def _get_tipo_doc(invo):
                tipo = "Anulado"
                if invo.state != 'cancel':
                    if invo.invoice_date < invo.invoice_date_due:
                        tipo = "Credito"
                    else:
                        tipo = "Contado"
                return tipo

            if tipo == 'compra':
                TABLE_DATA_FACTURAS.append([
                    str(cont),
                    str(i.invoice_date.strftime("%d/%m/%y")),
                    str(i.partner_id.name),
                    str(i.partner_id.vat),
                    _get_tipo_doc(i),
                    str(i.timbrado_id.name) if i.timbrado_id else ' ',
                    str(i.ref) if i.ref else '',

                    '{0:,.0f}'.format(int(base10)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(iva10)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(base5)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(iva5)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(exentas)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(total_factura)).replace(',', '.') if i.state != 'cancel' else "0"
                ])
            else:
                TABLE_DATA_FACTURAS.append([
                    str(cont),
                    str(i.invoice_date.strftime("%d/%m/%y")),
                    str(i.partner_id.name),
                    str(i.partner_id.vat),
                    _get_tipo_doc(i),
                    str(i.name),

                    '{0:,.0f}'.format(int(base10)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(iva10)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(base5)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(iva5)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(exentas)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(total_factura)).replace(',', '.') if i.state != 'cancel' else "0"
                ])

        if tipo == 'compra':
            TABLE_DATA_FACTURAS.append([' ', ' ', 'Total', ' ', ' ', ' ', ' ',
                                        '{0:,.0f}'.format(int(total_gral_base10)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_iva10)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_base5)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_iva5)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_exentas)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_total)).replace(',', '.')
                                        ])
        if tipo == 'venta':
            TABLE_DATA_FACTURAS.append([' ', ' ', 'Total', ' ', ' ', ' ',
                                        '{0:,.0f}'.format(int(total_gral_base10)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_iva10)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_base5)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_iva5)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_exentas)).replace(',', '.'),
                                        '{0:,.0f}'.format(int(total_gral_total)).replace(',', '.')
                                        ])

        pdf.set_font("Arial", "", 6)
        if tipo == 'compra':
            widths = (5, 8, 20, 10, 9, 10, 15, 10, 10, 10, 10, 10, 10)
        if tipo == 'venta':
            widths = (5, 8, 20, 10, 9, 15, 10, 10, 10, 10, 10, 10)
        with pdf.table(col_widths=widths
                ,
                       # borders_layout="SINGLE_TOP_LINE"
                       ) as table_facturas:
            for ir, data_row in enumerate(TABLE_DATA_FACTURAS):
                row = table_facturas.row()
                for ic, datum in enumerate(data_row):
                    if ic > 5 and ir > 0:
                        row.cell(text=datum, align='R')
                    else:
                        row.cell(datum)

        notas = []
        if tipo == 'compra':
            notas = self.env['account.move'].search([
                ('move_type', '=', 'out_refund'),
                ('state', 'in', ['posted', 'cancel']),
                ('invoice_date', '>=', self.fecha_inicio),
                ('invoice_date', '<=', self.fecha_fin),
                ('line_ids.tax_ids', '!=', False),
                ('company_id', '=', self.company_id.id)
            ])
            TABLE_DATA_NOTAS = [(
                'Nro',
                'Fecha',
                'Cliente',
                'RUC',
                'Tipo doc',
                'Nro Doc',
                "Gravadas 10%",  # "Importe Gravadas 10%",
                "IVA 10%",  # "Debito fiscal 10%",
                "Gravadas 5%",  # "Importe Gravadas 5%",
                "IVA 5%",  # "Debito fiscal 5%",
                "Exentas",  # "Importes Exentas",
                "Total"  # "Importe total facturado con IVA incluido",
            )]

        if tipo == 'venta':
            notas = self.env['account.move'].search([
                ('move_type', '=', 'in_refund'),
                ('state', 'in', ['posted']),
                ('invoice_date', '>=', self.fecha_inicio),
                ('invoice_date', '<=', self.fecha_fin),
                ('company_id', '=', self.company_id.id)
            ])

            TABLE_DATA_NOTAS = [(
                'Nro',
                'Fecha',
                'Proveedor',
                'RUC',
                'Tipo doc',
                'Timbrado',
                'Nro Doc',
                "Gravadas 10%",  # "Importe Gravadas 10%",
                "IVA 10%",  # "Debito fiscal 10%",
                "Gravadas 5%",  # "Importe Gravadas 5%",
                "IVA 5%",  # "Debito fiscal 5%",
                "Exentas",  # "Importes Exentas",
                "Total"  # "Importe total facturado con IVA incluido",
            )]

        pdf.set_font("Arial", "B", 10)
        if tipo == 'compra':
            pdf.cell(0, 5, "Notas de crédito emitidas", align="L", ln=True)
        if tipo == 'venta':
            pdf.cell(0, 5, "Notas de crédito recibidas", align="L", ln=True)
        pdf.cell(0, 5, "", align="L", ln=True)

        cont = 0
        total_gral_total = 0
        total_gral_base10 = 0
        total_gral_base5 = 0
        total_gral_iva10 = 0
        total_gral_iva5 = 0
        total_gral_exentas = 0
        for i in notas.sorted(key=lambda x: x.invoice_date):
            cont += 1
            total_factura = 0
            if i.state != 'cancel':
                total_factura = i.amount_total
            base10 = 0
            base5 = 0
            exentas = 0
            iva10 = 0
            iva5 = 0
            for t in i.filtered(lambda x: x.state != 'cancel').invoice_line_ids:
                if t.tax_ids and t.tax_ids[0].amount == 10:
                    base10 += t.price_total / 1.1
                    iva10 += t.price_total / 11
                if t.tax_ids and t.tax_ids[0].amount == 5:
                    base5 += t.price_total / 1.05
                    iva5 += t.price_total / 21
                if (t.tax_ids and t.tax_ids[0].amount == 0) or not t.tax_ids:
                    exentas += t.price_total
            # if not i.line_ids.tax_line_id and i.state !='cancel':
            #    exentas+=i.price_total

            if i.currency_id != self.company_id.currency_id:
                base10 = i.currency_id._convert(
                    base10, self.company_id.currency_id, self.company_id, i.invoice_date)
                iva10 = i.currency_id._convert(
                    iva10, self.company_id.currency_id, self.company_id, i.invoice_date)
                base5 = i.currency_id._convert(
                    base5, self.company_id.currency_id, self.company_id, i.invoice_date)
                iva5 = i.currency_id._convert(
                    iva5, self.company_id.currency_id, self.company_id, i.invoice_date)
                exentas = i.currency_id._convert(
                    exentas, self.company_id.currency_id, self.company_id, i.invoice_date)
                total_factura = i.currency_id._convert(
                    total_factura, self.company_id.currency_id, self.company_id, i.invoice_date)

            total_gral_total += total_factura
            total_gral_base10 += base10
            total_gral_base5 += base5
            total_gral_iva10 += iva10
            total_gral_iva5 += iva5
            total_gral_exentas += exentas

            def _get_tipo_doc(invo):
                tipo = " "
                if invo.state != 'cancel':
                    # tipo = "Nota de crédito"
                    tipo = "Nota crédito"
                return tipo

            if tipo == 'compra':
                TABLE_DATA_NOTAS.append([
                    str(cont),
                    str(i.invoice_date.strftime("%d/%m/%y")),
                    str(i.partner_id.name).strip(),
                    str(i.partner_id.vat).strip(),
                    _get_tipo_doc(i),
                    str(i.name),
                    '{0:,.0f}'.format(int(base10)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(iva10)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(base5)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(iva5)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(exentas)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(total_factura)).replace(',', '.') if i.state != 'cancel' else "0"
                ])
            if tipo == 'venta':
                TABLE_DATA_NOTAS.append([
                    str(cont),
                    str(i.invoice_date.strftime("%d/%m/%y")),
                    str(i.partner_id.name).strip(),
                    str(i.partner_id.vat).strip(),
                    _get_tipo_doc(i),
                    i.timbrado_id.name if i.timbrado_id else ' ',
                    str(i.ref),
                    '{0:,.0f}'.format(int(base10)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(iva10)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(base5)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(iva5)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(exentas)).replace(',', '.') if i.state != 'cancel' else "0",
                    '{0:,.0f}'.format(int(total_factura)).replace(',', '.') if i.state != 'cancel' else "0"
                ])
        if tipo == 'venta':
            TABLE_DATA_NOTAS.append([' ', ' ', 'Total', ' ', ' ', ' ', ' ',
                                     '{0:,.0f}'.format(int(total_gral_base10)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_iva10)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_base5)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_iva5)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_exentas)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_total)).replace(',', '.')
                                     ])
        if tipo == 'compra':
            TABLE_DATA_NOTAS.append([' ', ' ', 'Total', ' ', ' ', ' ',
                                     '{0:,.0f}'.format(int(total_gral_base10)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_iva10)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_base5)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_iva5)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_exentas)).replace(',', '.'),
                                     '{0:,.0f}'.format(int(total_gral_total)).replace(',', '.')
                                     ])
        pdf.set_font("Arial", "", 6)

        if tipo == 'venta':
            widths = (5, 8, 20, 10, 9, 10, 15, 10, 10, 10, 10, 10, 10)
        if tipo == 'compra':
            widths = (5, 8, 20, 10, 9, 15, 10, 10, 10, 10, 10, 10)
        with pdf.table(col_widths=widths) as table_notas:
            for ir, data_row in enumerate(TABLE_DATA_NOTAS):
                row = table_notas.row()
                for ic, datum in enumerate(data_row):
                    if ic > 5 and ir > 0:
                        row.cell(text=datum, align='R')
                    else:
                        row.cell(datum)

        pdf_bytes = None
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            pdf.output(tmp_file.name)

            with open(tmp_file.name, "rb") as file:
                pdf_bytes = file.read()
                self.page_qty = PyPDF2.PdfFileReader(file).numPages

        os.remove(tmp_file.name)
        pdf_base64 = base64.b64encode(pdf_bytes)
        self.archivo_nombre = "Libro_{0}.pdf".format(tipo)
        self.write({
            'archivo_rub': pdf_base64
        })

    def libro_mayor_pdf(self):
        # gl_obj = self.env['account.general.ledger.rubrica']
        facturas = self.env['account.move.line'].search([
            # ('move_type', '=', 'out_invoice'),
            ('parent_state', 'in', ['posted']),
            # ('date', '>=', self.fecha_inicio),
            ('date', '<=', self.fecha_fin),
            ('company_id', '=', self.company_id.id)
        ]
            , order=('id')
        )
        pdf = CustomPDF()
        pdf.set_font("Arial", "", 5)
        pdf.start_page_number = self.rubrica_id.nro_actual
        pdf.company = self.company_id
        pdf.titulo_enc = "Libro Mayor - Periodo: Del {0} al {1}".format(self.fecha_inicio.strftime('%d/%m/%Y'),
                                                                        self.fecha_fin.strftime('%d/%m/%Y'))
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)
        # pdf.set_font("Arial", "B", 10)
        pdf.add_page()
        # pdf.cell(40, 10, "Periodo: Del {0} al {1}".format(self.fecha_inicio, self.fecha_fin), align="L", ln=True)
        if not self.detallado:
            consulta = f"""
                select ml.account_id as cuenta_id, aa.name as nombre_cuenta, sum(ml.debit) as debit,
                sum(ml.credit) as credit, sum(ml.balance) as balance, aa.code as code
                FROM public.account_move_line as ml inner join account_account as aa on ml.account_id = aa.id
                where ml.date <= '{self.fecha_fin}' and ml.company_id = '{self.company_id.id}' and ml.parent_state = 'posted'
                group by ml.account_id, aa.name, aa.code order by ml.account_id, aa.code

            """

            self.env.cr.execute(consulta)
            results = self.env.cr.fetchall()
            # print("resultados; ", results)

            facturas_grouped = facturas.mapped('account_id')
            # print("facturas_grouped: ", facturas_grouped)
            TABLE_DATA = [(
                # 'Fecha',
                'Cuenta',
                'Debe',
                'Haber',
                'Saldo'
            )]
            # definiendo options con parametros basados en repote de account.report

            cont = 0
            total_credito = 0
            total_debito = 0
            total_balance = 0
            for row in results:
                cuenta_id, nombre_cuenta, debit, credit, balance, code = row

                debit = int(debit)
                credit = int(credit)
                balance = int(balance)
                print("hola: ", {cuenta_id}, {nombre_cuenta}, {debit}, {credit}, {balance})
                total_debito_t = debit
                total_credito_t = credit
                total_balance_t = balance
                TABLE_DATA.append([
                    str(code) + ' - ' + str(nombre_cuenta).replace('₲', '').strip(),  # cuenta contable
                    '{0:,.0f}'.format(int(debit)).replace(',', '.'),  # debito - DEBE
                    '{0:,.0f}'.format(int(credit)).replace(',', '.'),  # Credito - HABER
                    '{0:,.0f}'.format(int(balance)).replace(',', '.')  # balance

                ])
                total_debito += total_debito_t
                total_credito += total_credito_t
                total_balance += total_balance_t
            TABLE_DATA.append(['',
                               '{0:,.0f}'.format(int(total_debito)).replace(',', '.'),
                               '{0:,.0f}'.format(int(total_credito)).replace(',', '.'),
                               '{0:,.0f}'.format(int(total_balance)).replace(',', '.'),

                               ])

            TABLE_DATA = self.format_table_data(TABLE_DATA)

            # col_widths=(60, 15, 15, 15)
            with pdf.table(col_widths=(60, 15, 15, 15)) as table:
                for ir, data_row in enumerate(TABLE_DATA):
                    row = table.row()
                    for ic, datum in enumerate(data_row):
                        if ic > 0:  # La segunda, tercera y cuarta columnas son las tres últimas
                            row.cell(text=datum, align='R')
                        else:
                            row.cell(datum)
        else:
            TABLE_DATA = [(
                'Fecha',
                'Cuenta',
                'Referencia',
                'Debe',
                'Haber',
                'Saldo'
            )]
            consulta = f"""
                    WITH subconsulta AS (
                        SELECT
                            ml.account_id,
                            SUM(ml.debit) AS debit_total,
                            SUM(ml.credit) AS credit_total,
                            SUM(ml.balance) AS balance_total
                        FROM
                            public.account_move_line AS ml
                        WHERE
                            ml.date < '{self.fecha_inicio}' -- Fecha límite para fechas anteriores
                            AND ml.company_id = '{self.company_id.id}' 
                            and ml.parent_state = 'posted'
                        GROUP BY
                            ml.account_id
                    )
                    SELECT
                        ml.date as fecha,
                        ml.account_id AS cuenta_id,
                        aa.name as nombre_cuenta,
                        ml.name as nombre_linea_cuenta,
                        ml.debit as debit,
                        ml.credit as credit,
                        ml.balance as balance,
                        sub.debit_total as debit_total,
                        sub.credit_total as credit_total,
                        sub.balance_total as balance_total,
                        aa.id as codigo_cuenta,
                        am.name as referencia,
                        aa.code as code,
                        CASE
                            WHEN aa.name IS NOT NULL THEN 'Dentro del Rango'
                        END as estado_consulta,
                        ml.id as codigo_linea


                    FROM
                        public.account_move_line AS ml
                    INNER JOIN
                        account_account AS aa ON ml.account_id = aa.id
                    inner 
                        join account_move as am on ml.move_id = am.id 
                    LEFT JOIN
                        subconsulta as sub ON ml.account_id = sub.account_id
                    WHERE
                        ml.date >= '{self.fecha_inicio}'
                        AND ml.date <= '{self.fecha_fin}'
                        AND ml.company_id = '{self.company_id.id}' 
                        and ml.parent_state = 'posted'          
                    GROUP BY
                        ml.date, ml.account_id, aa.name, ml.name,sub.debit_total, sub.credit_total,sub.balance_total,
                        ml.debit,ml.credit,ml.balance,aa.id, am.name,aa.code, ml.id

                UNION

                    SELECT
                        NULL as fecha,
                        ml.account_id,
                        aa.name as nombre_cuenta,
                        Null as nombre_linea_cuenta,
                        0 as debit,
                        0 as credit,
                        0 as balance,
                        SUM(ml.debit) AS debit_total,
                        SUM(ml.credit) AS credit_total,
                        SUM(ml.balance) AS balance_total,
                        aa.id as codigo_cuenta,
                        NULL as referencia,
                        aa.code as code,
                        CASE
                            WHEN aa.name IS NOT NULL THEN 'Otras Cuentas'
                        END as estado_consulta,
                        NULL as codigo_linea
                    FROM
                        public.account_move_line AS ml
                    INNER JOIN
                        account_account AS aa ON ml.account_id = aa.id
                    WHERE
                        ml.date < '{self.fecha_inicio}'
                        AND ml.company_id = '{self.company_id.id}'
                        AND ml.parent_state = 'posted'
                        AND NOT EXISTS (
								SELECT 1
								FROM public.account_move_line AS ml_sub
								WHERE
									ml_sub.account_id = ml.account_id
									AND ml_sub.date >= '{self.fecha_inicio}'
									AND ml_sub.date <= '{self.fecha_fin}'
									AND ml_sub.company_id = '{self.company_id.id}'
									AND ml_sub.parent_state = 'posted'
							)
                    GROUP BY
                        ml.account_id, aa.name, aa.code, aa.id


                ORDER BY
                    ---ml.account_id, ml.date,aa.code
                    code, referencia
                    ---, fecha DESC;

            """

            self.env.cr.execute(consulta)
            results = self.env.cr.fetchall()
            # print("resultados2; ", results)
            cuenta_nombre_grupo = []

            for row in results:
                fecha, cuenta_id, nombre_cuenta, nombre_linea_cuenta, debit, credit, balance, debit_total, credit_total, balance_total, codigo_cuenta, referencia, code, estado_consulta, codigo_linea = row
                # print("linea: ", fecha, cuenta_id, nombre_cuenta, nombre_linea_cuenta, debit, credit, balance, debit_total, credit_total, balance_total,codigo_cuenta, referencia,code,estado_consulta)
                if cuenta_id not in [item['cuenta'] for item in cuenta_nombre_grupo]:
                    a = {
                        'cuenta': cuenta_id,
                        'nombre_cuenta': nombre_cuenta,
                        'debit_total': (debit_total),
                        'credit_total': (credit_total),
                        'balance_total': (balance_total),
                        'code': code,
                        'estado_consulta': estado_consulta

                    }
                    cuenta_nombre_grupo.append(a)
            # print("CUENTAS: ", cuenta_nombre_grupo)
            # for row in results:
            #     fecha, cuenta_id, nombre_cuenta, nombre_linea_cuenta, debit, credit, balance, debit_total, credit_total, balance_total,codigo_cuenta = row
            total_credito_final = 0
            total_debito_final = 0
            total_balance_final = 0

            total_debito_sin_detalle = 0  # Inicialización de la variable
            total_credito_sin_detalle = 0  # Puedes inicializar otras variables aquí
            total_balance_sin_detalle = 0  # Si es necesario

            for item in cuenta_nombre_grupo:
                total_credito = 0
                total_debito = 0
                total_balance = 0
                # print(cuenta_id, codigo_cuenta)
                if not item['debit_total']:
                    debit_total = 0
                else:
                    debit_total = item['debit_total']

                debit_total_saldo = debit_total

                if not item['credit_total']:
                    credit_total = 0
                else:
                    credit_total = item['credit_total']

                credit_total_saldo = credit_total

                if not item['balance_total']:
                    balance_total = 0
                else:
                    balance_total = item['balance_total']

                balance_total_saldo = balance_total

                TABLE_DATA.append([
                    '',
                    str(item['code']) + ' - ' + str(item['nombre_cuenta']).replace('₲', '').strip(),  # cuenta contable
                    '',
                    '',
                    '',
                    '',

                ])
                TABLE_DATA.append([
                    '',
                    'Saldo inicial',
                    '',
                    '{0:,.0f}'.format(int(debit_total)).replace(',', '.'),
                    '{0:,.0f}'.format(int(credit_total)).replace(',', '.'),
                    '{0:,.0f}'.format(int(balance_total)).replace(',', '.'),

                ])
                calculo_saldo_referencia = 0
                cont = 0
                for row in results:

                    fecha, cuenta_id, nombre_cuenta, nombre_linea_cuenta, debit, credit, balance, debit_total, credit_total, balance_total, codigo_cuenta, referencia, code, estado_consulta, codigo_linea = row
                    # print("cuenta_id: ", cuenta_id, "item['cuenta']: ", item['cuenta'], "estado_consulta: ", estado_consulta)
                    if item['estado_consulta'] == 'Dentro del Rango':
                        if cuenta_id == item['cuenta']:

                            if not nombre_linea_cuenta:
                                nombre_linea_cuenta = ''
                            else:
                                nombre_linea_cuenta = str(nombre_linea_cuenta).replace('₲', '').strip()
                            total_debito_t = debit
                            total_credito_t = credit
                            total_balance_t = balance
                            if not fecha:
                                fecha = ''
                            else:
                                fecha = str(fecha.strftime("%d/%m/%y"))
                            if referencia:
                                referencia = referencia
                            else:
                                referencia = ''
                            cont += 1

                            if cont == 1:
                                calculo_saldo_referencia = (balance_total_saldo + debit) - credit
                            else:
                                c = calculo_saldo_referencia
                                calculo_saldo_referencia = (c + debit) - credit

                            TABLE_DATA.append([
                                fecha,
                                '',
                                referencia,
                                '{0:,.0f}'.format(int(debit)).replace(',', '.'),
                                '{0:,.0f}'.format(int(credit)).replace(',', '.'),
                                '{0:,.0f}'.format(int(calculo_saldo_referencia)).replace(',', '.'),
                            ])
                            #             print("hola2")
                            total_debito += total_debito_t
                            total_credito += total_credito_t
                            total_balance += total_balance_t

                            total_debito_final += total_debito_t
                            total_credito_final += total_credito_t
                            total_balance_final += total_balance_t

                if item['estado_consulta'] == 'Dentro del Rango':

                    ## Sumamos el total del saldo incial y el total de las lineas de cuentas por cuentas
                    ###Debito
                    if debit_total_saldo > 0 and total_debito > 0:
                        total_debit_total_saldo_incial = debit_total_saldo + total_debito

                    elif debit_total_saldo > 0 and total_debito == 0:
                        total_debit_total_saldo_incial = debit_total_saldo

                    else:
                        total_debit_total_saldo_incial = total_debito
                    ####Credito
                    if credit_total_saldo > 0 and total_credito > 0:
                        total_credit_total_saldo_incial = credit_total_saldo + total_credito

                    elif credit_total_saldo > 0 and total_credito == 0:
                        total_credit_total_saldo_incial = credit_total_saldo

                    else:
                        total_credit_total_saldo_incial = total_credito

                    ###Saldo
                    if balance_total_saldo != 0 and total_balance != 0:
                        total_balance_total_saldo_incial = balance_total_saldo + total_balance
                    else:
                        total_balance_total_saldo_incial = total_balance

                    TABLE_DATA.append([' ',
                                       'Total ' + str(item['code']) + ' - ' + str(item['nombre_cuenta']).replace('₲',
                                                                                                                 '').strip(),
                                       # cuenta contable
                                       ' ',
                                       '{0:,.0f}'.format(int(total_debit_total_saldo_incial)).replace(',', '.'),
                                       '{0:,.0f}'.format(int(total_credit_total_saldo_incial)).replace(',', '.'),
                                       '{0:,.0f}'.format(int(total_balance_total_saldo_incial)).replace(',', '.'),

                                       ])
                else:
                    TABLE_DATA.append([' ',
                                       'Total ' + str(item['code']) + ' - ' + str(item['nombre_cuenta']).replace('₲',
                                                                                                                 '').strip(),
                                       # cuenta contable
                                       ' ',
                                       '{0:,.0f}'.format(int(debit_total_saldo)).replace(',', '.'),
                                       '{0:,.0f}'.format(int(credit_total_saldo)).replace(',', '.'),
                                       '{0:,.0f}'.format(int(balance_total_saldo)).replace(',', '.'),

                                       ])

            if debit_total_saldo > 0:
                resultado_debito = total_debito_sin_detalle + total_debito_final
            else:
                resultado_debito = total_debito_final

            if credit_total_saldo > 0:
                total_credito_sin_detalle += credit_total_saldo
                resultado_credito = total_credito_sin_detalle + total_credito_final
            else:
                resultado_credito = total_credito_final

            if balance_total_saldo != 0:
                total_balance_sin_detalle += balance_total_saldo
                resultado_balance = total_balance_sin_detalle + total_balance_final
            else:
                resultado_balance = total_balance_final

            # resultado_debito = total_debito_sin_detalle + total_debito_final
            # resultado_credito = total_credito_sin_detalle + total_credito_final
            # resultado_balance = total_balance_sin_detalle + total_balance_final
            TABLE_DATA.append([' ', ' ', ' ',
                               '{0:,.0f}'.format(int(resultado_debito)).replace(',', '.'),
                               '{0:,.0f}'.format(int(resultado_credito)).replace(',', '.'),
                               '{0:,.0f}'.format(int(resultado_balance)).replace(',', '.'),

                               ])

            TABLE_DATA = self.format_table_data(TABLE_DATA)

            with pdf.table(col_widths=(10, 50, 50, 15, 15, 15)) as table:
                for ir, data_row in enumerate(TABLE_DATA):
                    row = table.row()
                    for ic, datum in enumerate(data_row):
                        if ic >= 3:  # Alinea las últimas tres columnas a la derecha
                            row.cell(text=datum, align='R')
                        else:
                            row.cell(datum)

        pdf_bytes = None
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            pdf.output(tmp_file.name)

            with open(tmp_file.name, "rb") as file:
                pdf_bytes = file.read()
                self.page_qty = PyPDF2.PdfFileReader(file).numPages

        os.remove(tmp_file.name)
        pdf_base64 = base64.b64encode(pdf_bytes)
        self.archivo_nombre = "Libro_mayor.pdf"
        self.write({
            'archivo_rub': pdf_base64
        })

    def format_table_data(self, table_data):
        TABLE_DATA = [[cell.encode('utf-8') if isinstance(cell,str) else format_number_to_string(cell) for cell in sublist] for sublist in table_data]
        TABLE_DATA = [[cell.decode('utf-8') if isinstance(cell, str) else format_number_to_string(cell) for cell in sublist] for sublist in TABLE_DATA]
        TABLE_DATA = [[cell.replace('\u200b', '') for cell in sublist] for sublist in TABLE_DATA]
        TABLE_DATA = [[cell.replace('\u201c', '') for cell in sublist] for sublist in TABLE_DATA]
        TABLE_DATA = [[cell.replace('\u2013', '') for cell in sublist] for sublist in TABLE_DATA]
        TABLE_DATA = [[cell.replace('\u201d', '') for cell in sublist] for sublist in TABLE_DATA]
        TABLE_DATA = [[cell.replace('\u2022', '') for cell in sublist] for sublist in TABLE_DATA]
        return TABLE_DATA

    def libro_diario_pdf(self):
        TABLE_DATA = [('Cuenta', 'Descipción', 'Detalle', 'Crédito', 'Débito')]
        moves = self.env['account.move'].search(
            [('date', '>=', self.fecha_inicio), ('date', '<=', self.fecha_fin), ('state', '=', 'posted')])
        if moves:
            moves = moves.sorted(key=lambda x: (x.date, x.id))
        for move in moves:
            TABLE_DATA.append(('Asiento:{0} Fecha: {1}'.format(str(move.id).strip(),
                                                               str(move.date.strftime('%d/%m/%Y')).strip()), '', '', '',
                               ''))

            for line in move.line_ids:
                table_line = (
                    str(line.account_id.display_name if line.account_id.display_name else ' ').replace('₲', '').strip(),
                    str(line.name if line.name else ' ').replace('₲', '').strip(),
                    str(line.ref if line.ref else ' ').replace('₲', '').strip(),
                    '{0:,.0f}'.format(int(line.debit)).replace(',', '.') if line.debit else '0',
                    '{0:,.0f}'.format(int(line.credit)).replace(',', '.') if line.credit else '0'
                )
                TABLE_DATA.append(table_line)

        TABLE_DATA = self.format_table_data(TABLE_DATA)

        pdf = CustomPDF()
        pdf.set_font("Arial", "", 6)
        pdf.start_page_number = self.rubrica_id.nro_actual
        pdf.company = self.company_id
        pdf.titulo_enc = "Libro Diario"
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)
        pdf.add_page()

        with pdf.table(col_widths=(20, 30, 20, 10, 10)) as table:
            for ir, data_row in enumerate(TABLE_DATA):
                row = table.row()
                for ic, datum in enumerate(data_row):
                    if ic > 2 and ir > 0:
                        row.cell(text=datum, align='R')
                    else:
                        row.cell(datum)

        pdf_bytes = None
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            pdf.output(tmp_file.name)

            with open(tmp_file.name, "rb") as file:
                pdf_bytes = file.read()
                self.page_qty = PyPDF2.PdfFileReader(file).numPages

        os.remove(tmp_file.name)
        pdf_base64 = base64.b64encode(pdf_bytes)
        self.archivo_nombre = "Libro_diario.pdf"
        self.write({
            'archivo_rub': pdf_base64
        })

    def libro_diario_resumido_mensual_pdf(self):
        TABLE_DATA = [('Cuenta', 'Débito', 'Crédito')]
        moves = self.env['account.move'].search(
            [('date', '>=', self.fecha_inicio), ('date', '<=', self.fecha_fin), ('state', '=', 'posted')])

        if moves:
            anhos = set(moves.sorted(key=lambda x: x.date).mapped(lambda x: x.date.year))
            meses = set(moves.sorted(key=lambda x: x.date).mapped(lambda x: x.date.month))
            moves = moves.sorted(key=lambda x: (x.date, x.id))
            total_gral_debito = 0
            total_gral_credito = 0
            for anho in anhos:
                for mes in meses:
                    total_debito = 0
                    total_credito = 0
                    TABLE_DATA.append(('Fecha: %s/%s' % (mes, anho), '', ''))
                    month_moves = moves.filtered(lambda x: x.date.month == mes and x.date.year == anho)
                    month_move_lines_debits = month_moves.mapped('line_ids').filtered(lambda x: x.debit > 0)
                    month_move_lines_debits_accts = sorted(list(set(month_move_lines_debits.mapped('account_id'))),
                                                           key=lambda x: x.display_name)
                    for cuenta in month_move_lines_debits_accts:
                        debito = sum(month_move_lines_debits.filtered(lambda x: x.account_id == cuenta).mapped('debit'))
                        credito = sum(
                            month_move_lines_debits.filtered(lambda x: x.account_id == cuenta).mapped('credit'))
                        table_line = (
                            cuenta.display_name,
                            '{0:,.0f}'.format(debito),
                            '{0:,.0f}'.format(credito),
                        )
                        total_debito += debito
                        total_credito += credito
                        total_gral_debito += debito
                        total_gral_credito += credito
                        TABLE_DATA.append(table_line)
                    month_move_lines_credits = month_moves.mapped('line_ids').filtered(lambda x: x.credit > 0)
                    month_move_lines_credits_accts = sorted(list(set(month_move_lines_credits.mapped('account_id'))),
                                                            key=lambda x: x.display_name)
                    for cuenta in month_move_lines_credits_accts:
                        debito = sum(
                            month_move_lines_credits.filtered(lambda x: x.account_id == cuenta).mapped('debit'))
                        credito = sum(
                            month_move_lines_credits.filtered(lambda x: x.account_id == cuenta).mapped('credit'))
                        table_line = (
                            cuenta.display_name,
                            '{0:,.0f}'.format(
                                sum(month_move_lines_credits.filtered(lambda x: x.account_id == cuenta).mapped(
                                    'debit'))),
                            '{0:,.0f}'.format(
                                sum(month_move_lines_credits.filtered(lambda x: x.account_id == cuenta).mapped(
                                    'credit'))),
                        )
                        total_debito += debito
                        total_credito += credito
                        total_gral_debito += debito
                        total_gral_credito += credito
                        TABLE_DATA.append(table_line)
                    TABLE_DATA.append(('Total %s/%s' % (mes, anho), '{0:,.0f}'.format(total_debito),
                                       '{0:,.0f}'.format(total_credito)))
            TABLE_DATA.append(
                ('Total general', '{0:,.0f}'.format(total_gral_debito), '{0:,.0f}'.format(total_gral_credito)))

        pdf = CustomPDF()
        pdf.set_font("Arial", "", 6)
        pdf.start_page_number = self.rubrica_id.nro_actual
        pdf.company = self.company_id
        pdf.titulo_enc = "Libro Diario"
        pdf.subtitulo = "Del: %s al %s" % (self.fecha_inicio.strftime('%d/%m/%Y'), self.fecha_fin.strftime('%d/%m/%Y'))
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)
        pdf.add_page()

        TABLE_DATA = self.format_table_data(TABLE_DATA)

        with pdf.table(col_widths=(70, 15, 15)) as table:
            for ir, data_row in enumerate(TABLE_DATA):
                row = table.row()
                for ic, datum in enumerate(data_row):
                    if ic > 0:
                        row.cell(text=datum, align='R')
                    else:
                        row.cell(datum)

        pdf_bytes = None
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            pdf.output(tmp_file.name)

            with open(tmp_file.name, "rb") as file:
                pdf_bytes = file.read()
                self.page_qty = PyPDF2.PdfFileReader(file).numPages

        os.remove(tmp_file.name)
        pdf_base64 = base64.b64encode(pdf_bytes)
        self.archivo_nombre = "Libro_diario_resumido.pdf"

        self.write({
            'archivo_rub': pdf_base64
        })

    def libro_diario_resumido_dia_pdf(self):
        TABLE_DATA = [('Cuenta', 'Débito', 'Crédito')]
        moves = self.env['account.move'].search(
            [('date', '>=', self.fecha_inicio), ('date', '<=', self.fecha_fin), ('state', '=', 'posted')])

        if moves:
            anhos = set(moves.sorted(key=lambda x: x.date).mapped(lambda x: x.date.year))
            meses = set(moves.sorted(key=lambda x: x.date).mapped(lambda x: x.date.month))
            dias = set(moves.sorted(key=lambda x: x.date).mapped(lambda x: x.date.day))
            moves = moves.sorted(key=lambda x: (x.date, x.id))
            total_gral_debito = 0
            total_gral_credito = 0
            for anho in anhos:
                for mes in meses:
                    for dia in dias:
                        total_debito = 0
                        total_credito = 0
                        TABLE_DATA.append(('Fecha: %s/%s/%s' % (dia, mes, anho), '', ''))
                        day_moves = moves.filtered(
                            lambda x: x.date.month == mes and x.date.year == anho and x.date.day == dia)
                        day_move_lines_debits = day_moves.mapped('line_ids').filtered(lambda x: x.debit > 0)
                        day_move_lines_debits_accts = sorted(list(set(day_move_lines_debits.mapped('account_id'))),
                                                             key=lambda x: x.display_name)
                        for cuenta in day_move_lines_debits_accts:
                            debito = sum(
                                day_move_lines_debits.filtered(lambda x: x.account_id == cuenta).mapped('debit'))
                            credito = sum(
                                day_move_lines_debits.filtered(lambda x: x.account_id == cuenta).mapped('credit'))
                            table_line = (
                                cuenta.display_name,
                                '{0:,.0f}'.format(debito),
                                '{0:,.0f}'.format(credito),
                            )
                            total_debito += debito
                            total_credito += credito
                            total_gral_debito += debito
                            total_gral_credito += credito
                            TABLE_DATA.append(table_line)
                        day_move_lines_credits = day_moves.mapped('line_ids').filtered(lambda x: x.credit > 0)
                        day_move_lines_credits_accts = sorted(list(set(day_move_lines_credits.mapped('account_id'))),
                                                              key=lambda x: x.display_name)
                        for cuenta in day_move_lines_credits_accts:
                            debito = sum(
                                day_move_lines_credits.filtered(lambda x: x.account_id == cuenta).mapped('debit'))
                            credito = sum(
                                day_move_lines_credits.filtered(lambda x: x.account_id == cuenta).mapped('credit'))
                            table_line = (
                                cuenta.display_name,
                                '{0:,.0f}'.format(
                                    sum(day_move_lines_credits.filtered(lambda x: x.account_id == cuenta).mapped(
                                        'debit'))),
                                '{0:,.0f}'.format(
                                    sum(day_move_lines_credits.filtered(lambda x: x.account_id == cuenta).mapped(
                                        'credit'))),
                            )
                            total_debito += debito
                            total_credito += credito
                            total_gral_debito += debito
                            total_gral_credito += credito
                            TABLE_DATA.append(table_line)
                        TABLE_DATA.append(('Total %s/%s/%s' % (dia, mes, anho), '{0:,.0f}'.format(total_debito),
                                           '{0:,.0f}'.format(total_credito)))
            TABLE_DATA.append(
                ('Total general', '{0:,.0f}'.format(total_gral_debito), '{0:,.0f}'.format(total_gral_credito)))

        TABLE_DATA = self.format_table_data(TABLE_DATA)

        pdf = CustomPDF()
        pdf.set_font("Arial", "", 6)
        pdf.start_page_number = self.rubrica_id.nro_actual
        pdf.company = self.company_id
        pdf.titulo_enc = "Libro Diario"
        pdf.subtitulo = "Del: %s al %s" % (self.fecha_inicio.strftime('%d/%m/%Y'), self.fecha_fin.strftime('%d/%m/%Y'))
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)
        pdf.add_page()

        with pdf.table(col_widths=(70, 15, 15)) as table:
            for ir, data_row in enumerate(TABLE_DATA):
                row = table.row()
                for ic, datum in enumerate(data_row):
                    if ic > 0:
                        row.cell(text=datum, align='R')
                    else:
                        row.cell(datum)

        pdf_bytes = None
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            pdf.output(tmp_file.name)

            with open(tmp_file.name, "rb") as file:
                pdf_bytes = file.read()
                self.page_qty = PyPDF2.PdfFileReader(file).numPages

        os.remove(tmp_file.name)
        pdf_base64 = base64.b64encode(pdf_bytes)
        self.archivo_nombre = "Libro_diario_resumido.pdf"
        self.write({
            'archivo_rub': pdf_base64
        })

    def libro_inventario_pdf(self):
        debug_mode = False
        global expressions_totals  # El contenido de esta variable será calculado fuera de la función que imprime las líneas, por eso se declara como una variable global

        TABLE_DATA_bg = [
            [
                'Cantidad',
                'Detalle',
                'Precio Unitario',
                'Subtotal',
                'Total',
            ],
        ]
        if debug_mode:
            TABLE_DATA_bg[0] += ['--']
        TABLE_DATA_er = TABLE_DATA_bg.copy()

        previous_options = {
            'single_company': self.company_id.ids,
            'fiscal_position': 'all',
            'date': {
                'string': str(self.fecha_fin.year),
                'period_type': 'fiscalyear',
                'mode': 'range',
                'date_from': str(self.fecha_fin.year) + '-01-01',
                'date_to': str(self.fecha_fin.year) + '-12-31',
                'filter': 'custom'},
            'comparison': {'filter': 'no_comparison',
                           'number_period': 1,
                           'date_from': str(self.fecha_fin.year) + '-01-01',
                           'date_to': str(self.fecha_fin.year) + '-12-31',
                           'periods': []},
            'all_entries': False,
            'analytic': True,
            'unreconciled': True,
            'unfold_all': True,
            'analytic_groupby': True,
            'analytic_plan_groupby': True,
            'include_analytic_without_aml': False,
            'unposted_in_period': False
        }

        def print_account(
                env,
                expression_id,
                account_id,
                padding=0,
                hide_empty_lines=True,
        ):
            global expressions_totals
            table_lines = []
            table_line = []
            account_id_dict = expressions_totals[expression_id][account_id]
            if hide_empty_lines and \
                    not any(account_id_dict.get(balance_type) for balance_type in
                            ['account_balance', 'pending_outbound', 'pending_inbound']) and \
                    not debug_mode:
                return
            show_account_detail_mode = account_id_dict.get('show_account_detail_mode')
            table_line += [''] * padding
            table_line.append(account_id.code + ' - ' + account_id.name)
            if debug_mode:
                # table_line.append(account_id.id)
                table_line.append(show_account_detail_mode)
            if self.company_id.show_libro_inventario_base_report_bg_details:
                table_line += [''] * 2
            else:
                table_line += ['']
            table_line.append(account_id_dict.get('account_total'))
            if not self.company_id.show_libro_inventario_base_report_bg_details:
                table_line += ['']
            table_lines.append(table_line)
            if show_account_detail_mode == 'mode_account_balance':
                table_line = []
                table_line += [''] * padding
                table_line.append('Saldo Conciliado')
                table_line += ['']
                table_line.append(account_id_dict.get('account_balance'))
                table_line += ['']
                table_lines.append(table_line)
                table_line = []

                table_line += [''] * padding
                table_line.append('Pagos pendientes de conciliación')
                table_line += ['']
                table_line.append(account_id_dict.get('pending_outbound'))
                table_line += ['']
                table_lines.append(table_line)
                table_line = []

                table_line += [''] * padding
                table_line.append('Recibos pendientes de conciliación')
                table_line += ['']
                table_line.append(account_id_dict.get('pending_inbound'))
                table_line += ['']
                table_lines.append(table_line)
                table_line = []

            elif show_account_detail_mode == 'mode_account_partners':
                account_move_line_ids = account_id_dict.get('account_move_line_ids')
                if account_move_line_ids:
                    partner_ids = account_move_line_ids.mapped('partner_id')
                    partner_ids_list = list(partner_ids)
                    if account_id_dict.get('account_move_line_ids').filtered(lambda x: not x.partner_id):
                        partner_ids_list.append(partner_ids.browse())
                    for partner_id in partner_ids_list:
                        table_line = []
                        account_move_line_ids_partner = account_id_dict.get('account_move_line_ids').filtered(
                            lambda x: x.partner_id == partner_id
                        )
                        table_line += [''] * padding
                        table_line.append(partner_id.name if partner_id else 'Sin nombre')
                        table_line.append(sum(
                            account_move_line.amount_residual for account_move_line in account_move_line_ids_partner))
                        table_line += [''] * 2
                        table_lines.append(table_line)
            elif show_account_detail_mode == 'mode_account_inventory':
                if env.ref('base.module_stock').state in ['installed', 'to upgrade']:
                    stock_valuation_layer_ids = env['stock.valuation.layer'].search([
                        ('product_id.categ_id.property_stock_valuation_account_id', '=', account_id.id),
                    ])
                    for product_id in stock_valuation_layer_ids.product_id:
                        table_line = []
                        stock_valuation_layers_product_id = stock_valuation_layer_ids.filtered(
                            lambda x: x.product_id == product_id)

                        stock_valuation_layers_product_id_quantity = sum(
                            stock_valuation_layer_product_id.quantity for stock_valuation_layer_product_id in
                            stock_valuation_layers_product_id
                        )

                        stock_valuation_layers_product_id_value = sum(
                            stock_valuation_layer_product_id.value for stock_valuation_layer_product_id in
                            stock_valuation_layers_product_id
                        )

                        stock_valuation_layers_product_id_unit_cost = 0
                        if stock_valuation_layers_product_id_value and stock_valuation_layers_product_id_quantity:
                            stock_valuation_layers_product_id_unit_cost = stock_valuation_layers_product_id_value / stock_valuation_layers_product_id_quantity

                        table_line += [''] * (padding - 1)
                        table_line.append(stock_valuation_layers_product_id_quantity)
                        table_line.append(product_id.name)
                        table_line.append(stock_valuation_layers_product_id_unit_cost)
                        table_line.append(stock_valuation_layers_product_id_value)
                        table_line += ['']
                        table_lines.append(table_line)
            elif show_account_detail_mode == 'mode_account_asset_fixed':
                account_assets = env['account.asset'].search([
                    ('state', 'in', ['open', 'close']),
                    ('account_asset_id', '=', account_id.id),
                ])
                for account_asset in account_assets:
                    table_line = []
                    table_line += [''] * padding
                    table_line.append(account_asset.name)
                    if account_asset.state == 'open' and not account_id.asset_model:
                        table_line.append(account_asset.original_value)
                    elif account_asset.state == 'close' or \
                            account_asset.state == 'open' and account_id.asset_model:
                        table_line.append(account_asset.book_value)
                    table_line += [''] * 2
                    table_lines.append(table_line)
            for table_line in table_lines:
                TABLE_DATA.append(table_line)

        def print_accounts_by_group(
                env,
                expression_id,
                padding,
                hide_empty_lines,
                group_ids,
                allowed_account_group_ids,
                account_ids,
        ):
            for group_id in group_ids:
                child_group_ids = group_ids.search(
                    [('parent_id', '=', group_id.id), ('id', 'in', allowed_account_group_ids.ids)])
                for account_group_id in child_group_ids:
                    table_line = []
                    account_group_for_total_ids = account_group_id
                    while True:
                        account_group_child_ids = account_group_for_total_ids.search([
                            ('parent_id', 'in', account_group_for_total_ids.ids),
                            ('id', 'not in', account_group_for_total_ids.ids),
                        ])
                        if account_group_child_ids:
                            account_group_for_total_ids |= account_group_child_ids
                        else:
                            break

                    account_group_total = sum([
                        expressions_totals[expression_id][account_id].get('account_total') for account_id in
                        account_ids.search([
                            ('id', 'in', account_ids.ids),
                            ('group_id', 'in', account_group_for_total_ids.ids),
                        ])
                    ])

                    table_line += [''] * padding
                    table_line.append(account_group_id.code_prefix_start + ' - ' + account_group_id.name)
                    table_line += [''] * 2
                    table_line.append(account_group_total)
                    TABLE_DATA.append(table_line)
                    for account_id in account_ids.filtered(lambda account: account.group_id == account_group_id):
                        print_account(
                            env=env,
                            expression_id=expression_id,
                            account_id=account_id,
                            padding=padding,
                            hide_empty_lines=hide_empty_lines,
                        )
                    print_accounts_by_group(
                        env=env,
                        expression_id=expression_id,
                        padding=padding,
                        hide_empty_lines=hide_empty_lines,
                        group_ids=account_group_id,
                        allowed_account_group_ids=allowed_account_group_ids,
                        account_ids=account_ids,
                    )

        def print_report_lines(
                env,
                report_lines,
                padding,
                headers,
                quantity_headers,
                hide_empty_lines,
                force_print_from_report_totals,
                force_report_totals,
                account_report_id,
        ):
            subformula_field = ''
            if release.major_version in ['16.0']:
                subformula_field = 'subformula'
            if release.major_version in ['15.0']:
                subformula_field = 'formulas'

            global expressions_totals

            if headers:
                headers = False

            for report_line in report_lines:
                foldable = False
                if release.major_version in ['16.0']:
                    foldable = report_line.foldable
                if release.major_version in ['15.0']:
                    foldable = report_line.show_domain == foldable

                expression_ids = False
                if release.major_version in ['16.0']:
                    expression_ids = report_line.expression_ids
                if release.major_version in ['15.0']:
                    expression_ids = report_line.children_ids
                if force_print_from_report_totals and \
                        force_report_totals or \
                        (
                                force_report_totals and
                                ('cross_report' in [expression_id[subformula_field] for expression_id in
                                                    expression_ids]) or
                                (not foldable and not report_line.hide_if_zero)
                        ):
                    report_line_total = 0
                    if force_report_totals:
                        for clave in force_report_totals:
                            # Verifica si la clave está en el otro diccionario
                            if clave in expression_ids.ids:
                                # Suma el valor correspondiente
                                report_line_total += force_report_totals[clave]['value']

                        #report_line_total = sum(
                        #    force_report_totals.get('value') for expression_id in expression_ids
                        #)
                else:
                    report_line_total = sum(
                        sum(
                            expressions_totals[expression_id][account_id].get('account_total')
                            for account_id in expressions_totals[expression_id]
                        )
                        for expression_id in
                        report_line.search([('id', 'child_of', report_line.ids)]).children_ids.filtered(
                            lambda x: x.domain)
                    )

                if hide_empty_lines and not report_line_total and not debug_mode:
                    continue
                table_line = []
                table_line += [''] * padding
                table_line.append(report_line.name)
                if debug_mode: table_line.append(report_line.id)  # SOLO PRESENTE EN MODO DEBUG
                table_line += [''] * 2
                table_line.append(report_line_total)

                report_line_expressions = []
                if release.major_version in ['16.0']:
                    report_line_expressions = report_line.expression_ids.filtered(lambda
                                                                                      x: x.engine == 'domain')  # Se filtran las expresiones de las líneas que forman la estructura del reporte, solo se usarán las expresiones que usen 'domain' para el cálculo de su contenido
                if release.major_version in ['15.0']:
                    report_line_expressions = report_line.children_ids.filtered(lambda
                                                                                    x: x.domain)  # Se filtran las expresiones de las líneas que forman la estructura del reporte, solo se usarán las expresiones que usen 'domain' para el cálculo de su contenido

                TABLE_DATA.append(table_line)
                for expression_id in report_line_expressions:
                    if account_report_id.filter_hierarchy == 'by_default':
                        account_ids = env['account.account'].browse([a.id for a in expressions_totals[expression_id]])
                        account_group_ids = account_ids.group_id
                        while True:
                            account_group_parent_ids = account_group_ids.parent_id.filtered(
                                lambda x: x not in account_group_ids)
                            if account_group_parent_ids:
                                account_group_ids |= account_group_parent_ids
                            else:
                                break
                        root_group_ids = account_group_ids.filtered(lambda x: not x.parent_id)

                        print_accounts_by_group(
                            env=env,
                            expression_id=expression_id,
                            padding=padding,
                            hide_empty_lines=hide_empty_lines,
                            group_ids=root_group_ids,
                            allowed_account_group_ids=account_group_ids,
                            account_ids=account_ids,
                        )
                    else:
                        for account_id in expressions_totals[expression_id]:
                            print_account(
                                env,
                                expression_id,
                                account_id,
                                padding=padding,
                                hide_empty_lines=hide_empty_lines,
                            )
                print_report_lines(
                    env=env,
                    report_lines=report_line.children_ids,
                    padding=padding,
                    headers=headers,
                    quantity_headers=quantity_headers,
                    hide_empty_lines=hide_empty_lines,
                    force_print_from_report_totals=force_print_from_report_totals,
                    force_report_totals=force_report_totals,
                    account_report_id=account_report_id,
                )

        #
        #
        #
        #
        # BALANCE GENERAL
        #
        #
        #
        #
        TABLE_DATA = TABLE_DATA_bg
        account_financial_report_bg_l10n_py = self.company_id.reporte_libro_inventario_base_report_bg
        if not account_financial_report_bg_l10n_py:
            raise exceptions.ValidationError(
                'No está establecido un reporte base para el Balance General del reporte Libro Inventario, vaya a la configuración de contabilidad para establecer los parámetros necesarios')
        account_financial_report_bg_l10n_py_report_informations = False
        if release.major_version in ['16.0']:
            account_financial_report_bg_l10n_py_report_informations = account_financial_report_bg_l10n_py.get_report_informations(
                previous_options)
            account_financial_report_bg_l10n_py_report_informations = account_financial_report_bg_l10n_py_report_informations.get(
                'column_groups_totals')
            account_financial_report_bg_l10n_py_report_informations = account_financial_report_bg_l10n_py_report_informations.get(
                list(account_financial_report_bg_l10n_py_report_informations.keys())[0]
            )
        if release.major_version in ['15.0']:
            previous_options = account_financial_report_bg_l10n_py._get_options(previous_options)
            account_financial_report_bg_l10n_py_report_informations = account_financial_report_bg_l10n_py._get_table(
                previous_options)
            account_financial_report_bg_l10n_py_report_informations = {
                x.get('model_ref')[1]: {'value': x.get('columns')[0].get('no_format')} for x in
                account_financial_report_bg_l10n_py_report_informations[1] if x.get('model_ref')}

        expressions_totals = {}  # Acá irán todos los valores de las cuentas a imprimir
        expression_ids = []
        if release.major_version in ['16.0']:
            expression_ids = account_financial_report_bg_l10n_py.line_ids.expression_ids.filtered(lambda
                                                                                                      x: x.engine == 'domain')  # Se filtran las expresiones de las líneas que forman la estructura del reporte, solo se usarán las expresiones que usen 'domain' para el cálculo de su contenido
        if release.major_version in ['15.0']:
            expression_ids = account_financial_report_bg_l10n_py.line_ids.search([
                ('id', 'child_of', account_financial_report_bg_l10n_py.line_ids.ids)
            ]).filtered(lambda
                            x: x.domain)  # Se filtran las expresiones de las líneas que forman la estructura del reporte, solo se usarán las expresiones que usen 'domain' para el cálculo de su contenido
        for expression_id in expression_ids:
            expressions_totals[expression_id] = {}
            aml_ids = self.env['account.move.line']
            if release.major_version in ['16.0']:
                if expression_id.formula:
                    aml_ids = eval(
                        "self.env['account.move.line'].search(" + expression_id.formula + ")")  # Cada expresión a procesar tiene un dominio para obtener los apuntes contables, de los cuales se deben obtener las cuentas a preocesar
            if release.major_version in ['15.0']:
                if expression_id.domain:
                    aml_ids = eval(
                        "self.env['account.move.line'].search(" + expression_id.domain + ")")  # Cada expresión a procesar tiene un dominio para obtener los apuntes contables, de los cuales se deben obtener las cuentas a preocesar
            account_ids = self.env['account.account']
            if release.major_version in ['16.0']:
                account_ids = aml_ids.mapped('account_id').filtered(
                    lambda x:
                    x.account_type in [
                        'asset_cash',
                        'asset_receivable',
                        'asset_current',
                        'asset_non_current',
                        'asset_fixed',
                        'liability_payable',
                        'liability_current',
                        'liability_non_current',
                        'equity',
                    ]
                    and x not in (
                        x.company_id.account_journal_payment_debit_account_id,
                        x.company_id.account_journal_payment_credit_account_id,
                    )
                ).sorted(key=lambda x: x.code)
            if release.major_version in ['15.0']:
                account_ids = aml_ids.mapped('account_id').filtered(
                    lambda x:
                    x.user_type_id in [
                        self.env.ref('account.data_account_type_liquidity'),
                        self.env.ref('account.data_account_type_receivable'),
                        self.env.ref('account.data_account_type_current_assets'),
                        self.env.ref('account.data_account_type_non_current_assets'),
                        self.env.ref('account.data_account_type_fixed_assets'),
                        self.env.ref('account.data_account_type_payable'),
                        self.env.ref('account.data_account_type_current_liabilities'),
                        self.env.ref('account.data_account_type_non_current_liabilities'),
                        self.env.ref('account.data_account_type_equity'),
                    ]
                    and x not in (
                        x.company_id.account_journal_payment_debit_account_id,
                        x.company_id.account_journal_payment_credit_account_id,
                    )
                ).sorted(key=lambda x: x.code)

            for account_id in account_ids:

                # BALANCE A LA FECHA
                account_move_line_ids = aml_ids.search([
                    ('account_id', '=', account_id.id),
                    ('parent_state', '=', 'posted'),
                    ('date', '<=', previous_options['date']['date_to'])
                ])
                if account_move_line_ids:
                    account_balance = sum(account_move_line_ids.mapped('balance'))
                else:
                    account_balance = 0
                account_outbound = 0
                account_inbound = 0
                amount_field = 'amount_company_currency_signed'
                if release.major_version in ['16.0']:
                    amount_field = 'amount_company_currency_signed'
                if release.major_version in ['15.0']:
                    amount_field = 'amount'
                for move_type in ['outbound', 'inbound']:
                    self.env.cr.execute("""
                                SELECT SUM(""" + amount_field + """) AS amount_total_company
                                  FROM account_payment payment
                                  JOIN account_move move ON move.payment_id = payment.id
                                 WHERE payment.is_matched IS NOT TRUE
                                   AND payment.payment_type = %s
                                   AND move.state = 'posted'
                                   AND move.journal_id = ANY(%s)
                              GROUP BY move.company_id, move.journal_id, move.currency_id
                            """, [move_type, self.env['account.journal'].search(
                        [('default_account_id', '=',
                          account_id.id)]).ids])  # Debemos obtener todos los saldos pendientes de conciliar para la cuenta
                    query_result = self.env.cr.fetchall()
                    amount_result = sum(sum(j for j in t) for t in query_result)
                    if move_type == 'outbound':
                        account_outbound = -amount_result
                    if move_type == 'inbound':
                        account_inbound = amount_result

                # Determinamos qué modo de detalles va a tener la cuenta.
                # En el modo 'mode_account_balance' se detalla el saldo conciliado, y los pendientes de conciliación de entrada y salida.
                # En el modo 'mode_account_partners' se detalla los saldos pendientes de conciliación pero agrupados por proveedor o cliente.
                # En el modo 'mode_account_inventory' se detalla la valoración de inventario.
                # En el modo 'mode_account_asset_fixed' se detalla la valoración de los activos fijos.
                show_account_detail_mode = False
                if release.major_version in ['16.0']:
                    account_type = account_id.account_type
                    if self.company_id.show_libro_inventario_base_report_bg_details:
                        if account_type == 'asset_cash' and not account_id.reconcile:
                            show_account_detail_mode = 'mode_account_balance'

                        elif (account_type == 'asset_receivable' and account_id.reconcile) or \
                                (account_type == 'liability_payable' and account_id.reconcile):
                            show_account_detail_mode = 'mode_account_partners'

                        elif account_type == 'asset_current' and not account_id.reconcile and account_id.create_asset in [
                            'no']:
                            show_account_detail_mode = 'mode_account_inventory'

                        elif (account_type == 'asset_fixed') or \
                                (account_type == 'liability_current') or \
                                (
                                        account_type == 'asset_current' and
                                        not account_id.reconcile and
                                        account_id.create_asset in ['draft', 'validate'] and
                                        account_id.asset_model
                                ):
                            show_account_detail_mode = 'mode_account_asset_fixed'
                if release.major_version in ['15.0']:
                    account_user_type = account_id.user_type_id
                    if self.company_id.show_libro_inventario_base_report_bg_details:
                        if account_user_type == self.env.ref(
                                'account.data_account_type_liquidity') and not account_id.reconcile:
                            show_account_detail_mode = 'mode_account_balance'

                        elif (account_user_type == self.env.ref(
                                'account.data_account_type_receivable') and account_id.reconcile) or \
                                (account_user_type == self.env.ref(
                                    'account.data_account_type_payable') and account_id.reconcile):
                            show_account_detail_mode = 'mode_account_partners'

                        elif account_user_type == self.env.ref(
                                'account.data_account_type_current_assets') and not account_id.reconcile and account_id.create_asset in [
                            'no']:
                            show_account_detail_mode = 'mode_account_inventory'

                        elif (account_user_type == self.env.ref('account.data_account_type_fixed_assets')) or \
                                (account_user_type == self.env.ref('account.data_account_type_current_liabilities')) or \
                                (
                                        account_user_type == self.env.ref(
                                    'account.data_account_type_current_assets') and
                                        not account_id.reconcile and
                                        account_id.create_asset in ['draft', 'validate'] and
                                        account_id.asset_model
                                ):
                            show_account_detail_mode = 'mode_account_asset_fixed'

                subformula = ''
                if release.major_version in ['16.0']:
                    subformula = expression_id.subformula
                if release.major_version in ['15.0']:
                    subformula = expression_id.formulas

                if subformula == '-sum':
                    account_balance *= -1
                    account_inbound *= -1
                    account_outbound *= -1

                expressions_totals[expression_id][account_id] = {
                    'account_total': account_balance + account_inbound - account_outbound,
                    'account_move_line_ids': account_move_line_ids,
                    'account_balance': account_balance,
                    'pending_outbound': account_outbound,
                    'pending_inbound': account_inbound,
                    'show_account_detail_mode': show_account_detail_mode,
                }

        print_report_lines(
            env=self.env,
            report_lines=account_financial_report_bg_l10n_py.line_ids.filtered(lambda x: not x.parent_id),
            padding=1,
            headers=True,
            quantity_headers=True,
            hide_empty_lines=True,
            force_print_from_report_totals=False,
            force_report_totals=account_financial_report_bg_l10n_py_report_informations,
            account_report_id=account_financial_report_bg_l10n_py,
        )

        # addSalto(6)
        #
        #
        #
        #
        # ESTADO DE RESULTADOS
        #
        #
        #
        #
        TABLE_DATA = TABLE_DATA_er
        account_financial_report_er_l10n_py = self.company_id.reporte_libro_inventario_base_report_er
        if not account_financial_report_er_l10n_py:
            raise exceptions.ValidationError(
                'No está establecido un reporte base para el Estado de Resultados del reporte Libro Inventario, vaya a la configuración de contabilidad para establecer los parámetros necesarios')
        account_financial_report_er_l10n_py_report_informations = False
        if release.major_version in ['16.0']:
            account_financial_report_er_l10n_py_report_informations = account_financial_report_er_l10n_py.get_report_informations(
                previous_options)
            account_financial_report_er_l10n_py_report_informations = account_financial_report_er_l10n_py_report_informations.get(
                'column_groups_totals')
            account_financial_report_er_l10n_py_report_informations = account_financial_report_er_l10n_py_report_informations.get(
                list(account_financial_report_er_l10n_py_report_informations.keys())[0]
            )
        if release.major_version in ['15.0']:
            previous_options = account_financial_report_er_l10n_py._get_options(previous_options)
            account_financial_report_er_l10n_py_report_informations = account_financial_report_er_l10n_py._get_table(
                previous_options)
            account_financial_report_er_l10n_py_report_informations = {
                x.get('model_ref')[1]: {'value': x.get('columns')[0].get('no_format')} for x in
                account_financial_report_er_l10n_py_report_informations[1] if x.get('model_ref')}

        # simpleWrite('ESTADO DE RESULTADOS PRACTICADO AL 31 DE DICIEMBRE DE ' + str(wizard.year), bold)
        expressions_totals = {}  # Acá irán todos los valores de las cuentas a imprimir

        expression_ids = []
        if release.major_version in ['16.0']:
            expression_ids = account_financial_report_er_l10n_py.line_ids.expression_ids.filtered(lambda
                                                                                                      x: x.engine == 'domain')  # Se filtran las expresiones de las líneas que forman la estructura del reporte, solo se usarán las expresiones que usen 'domain' para el cálculo de su contenido
        if release.major_version in ['15.0']:
            expression_ids = account_financial_report_er_l10n_py.line_ids.search([
                ('id', 'child_of', account_financial_report_er_l10n_py.line_ids.ids)
            ]).filtered(lambda
                            x: x.domain)  # Se filtran las expresiones de las líneas que forman la estructura del reporte, solo se usarán las expresiones que usen 'domain' para el cálculo de su contenido
        for expression_id in expression_ids:
            expressions_totals[expression_id] = {}
            aml_ids = self.env['account.move.line']
            if release.major_version in ['16.0']:
                if expression_id.formula:
                    aml_ids = eval(
                        "self.env['account.move.line'].search(" + expression_id.formula + ")")  # Cada expresión a procesar tiene un dominio para obtener los apuntes contables, de los cuales se deben obtener las cuentas a preocesar
            if release.major_version in ['15.0']:
                if expression_id.domain:
                    aml_ids = eval(
                        "self.env['account.move.line'].search(" + expression_id.domain + ")")  # Cada expresión a procesar tiene un dominio para obtener los apuntes contables, de los cuales se deben obtener las cuentas a preocesar
            account_ids = self.env['account.account']
            if release.major_version in ['16.0']:
                account_ids = aml_ids.mapped('account_id').filtered(
                    lambda x:
                    x.account_type in [
                        'income',
                        'expense',
                        'expense_depreciation',
                        'income_other',
                    ]
                    and x not in (
                        x.company_id.account_journal_payment_debit_account_id,
                        x.company_id.account_journal_payment_credit_account_id,
                    )
                ).sorted(key=lambda x: x.code)
            if release.major_version in ['15.0']:
                account_ids = aml_ids.mapped('account_id').filtered(
                    lambda x:
                    True or
                    x.user_type_id.internal_group in [
                        'income',
                        'expense',
                        'expense_depreciation',
                        'income_other',
                    ]
                    and x not in (
                        x.company_id.account_journal_payment_debit_account_id,
                        x.company_id.account_journal_payment_credit_account_id,
                    )
                ).sorted(key=lambda x: x.code)

            for account_id in account_ids:

                # BALANCE A LA FECHA
                account_move_line_ids = aml_ids.search([
                    ('account_id', '=', account_id.id),
                    ('parent_state', '=', 'posted'),
                    ('date', '<=', previous_options['date']['date_to'])
                ])
                if account_move_line_ids:
                    account_balance = sum(account_move_line_ids.mapped('balance'))
                else:
                    account_balance = 0
                account_outbound = 0
                account_inbound = 0
                amount_field = 'amount_company_currency_signed'
                if release.major_version in ['16.0']:
                    amount_field = 'amount_company_currency_signed'
                if release.major_version in ['15.0']:
                    amount_field = 'amount'
                for move_type in ['outbound', 'inbound']:
                    self.env.cr.execute("""
                                SELECT SUM(""" + amount_field + """) AS amount_total_company
                                  FROM account_payment payment
                                  JOIN account_move move ON move.payment_id = payment.id
                                 WHERE payment.is_matched IS NOT TRUE
                                   AND payment.payment_type = %s
                                   AND move.state = 'posted'
                                   AND move.journal_id = ANY(%s)
                              GROUP BY move.company_id, move.journal_id, move.currency_id
                            """, [move_type, self.env['account.journal'].search(
                        [('default_account_id', '=',
                          account_id.id)]).ids])  # Debemos obtener todos los saldos pendientes de conciliar para la cuenta
                    query_result = self.env.cr.fetchall()
                    amount_result = sum(sum(j for j in t) for t in query_result)
                    if move_type == 'outbound':
                        account_outbound = -amount_result
                    if move_type == 'inbound':
                        account_inbound = amount_result

                show_account_detail_mode = False

                subformula = ''
                if release.major_version in ['16.0']:
                    subformula = expression_id.subformula
                if release.major_version in ['15.0']:
                    subformula = expression_id.formulas

                if subformula == '-sum':
                    account_balance *= -1
                    account_inbound *= -1
                    account_outbound *= -1

                expressions_totals[expression_id][account_id] = {
                    'account_total': account_balance + account_inbound - account_outbound,
                    'account_move_line_ids': account_move_line_ids,
                    'account_balance': account_balance,
                    'pending_outbound': account_outbound,
                    'pending_inbound': account_inbound,
                    'show_account_detail_mode': show_account_detail_mode,
                }

        print_report_lines(
            env=self.env,
            report_lines=account_financial_report_er_l10n_py.line_ids.filtered(lambda x: not x.parent_id),
            padding=1,
            headers=True,
            quantity_headers=False,
            hide_empty_lines=True,
            force_print_from_report_totals=True,
            force_report_totals=account_financial_report_er_l10n_py_report_informations,
            account_report_id=account_financial_report_er_l10n_py,
        )

        pdf = CustomPDF()
        pdf.set_font("Arial", "", 6)
        pdf.start_page_number = self.rubrica_id.nro_actual
        pdf.company = self.company_id
        if self.rubrica_id.imagen:
            pdf.rub_img = base64.b64decode(self.rubrica_id.imagen)
        col_widths = (10, 50, 10, 10, 10)
        if debug_mode:
            col_widths += (10,)
        for TABLE_DATA in [TABLE_DATA_bg, TABLE_DATA_er]:
            if TABLE_DATA == TABLE_DATA_bg:
                pdf.titulo_enc = "Libro Inventario - Balance General"
            if TABLE_DATA == TABLE_DATA_er:
                pdf.titulo_enc = "Libro Inventario - Estado de Resultados"
            pdf.add_page()
            with pdf.table(col_widths=col_widths) as table:
                for line_count, data_row in enumerate(TABLE_DATA):
                    row = table.row()
                    for column_count, data in enumerate(data_row):
                        if column_count > 1 and line_count > 0:
                            row.cell(text=format_number_to_string(data), align='R')
                        else:
                            if data and isinstance(data, str) and '\u2013' in data:
                                print('si')
                                data = data.replace('\u2013','')
                            row.cell(text=str(data), align='L')

        pdf_bytes = None
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            pdf.output(tmp_file.name)

            with open(tmp_file.name, "rb") as file:
                pdf_bytes = file.read()
                self.page_qty = PyPDF2.PdfFileReader(file).numPages

        os.remove(tmp_file.name)
        pdf_base64 = base64.b64encode(pdf_bytes)
        self.archivo_nombre = "Libro_inventario.pdf"
        self.write({
            'archivo_rub': pdf_base64
        })


class CustomPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.start_page_number = 0
        self.rub_img = None
        self.company = None
        self.titulo_enc = ''
        self.subtitulo = False

    def header(self, data=None):
        self.set_font("Arial", "B", 10)
        if self.rub_img:
            self.image(self.rub_img, 165, 10, 45)
        self.cell(0, 2, self.company.name, align="L")
        self.cell(-20, 2, f"Nro: {self.start_page_number + self.page_no()}", align="R", ln=True)
        self.cell(0, 5, self.company.vat, align="L", ln=True)
        self.cell(0, 5, self.company.street if self.company.street else '', align="L", ln=True)
        # self.cell(0, 10, txt=self.company.name, align="L")
        # self.cell(0, 5, f"Nro: {self.start_page_number + self.page_no()}", align="R", ln=True)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, self.titulo_enc, align="C", ln=True)
        if self.subtitulo:
            self.cell(0, 10, self.subtitulo, align="C", ln=True)