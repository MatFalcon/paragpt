# -*- coding: utf-8 -*-

import datetime

from odoo import api, exceptions, fields, models


class EmisionesCustodia(models.Model):
    _name = 'emisiones.emisiones_custodia'
    _description = 'Tabla para emisión custodia'

    name = fields.Char(string="Nombre")
    product_custodia_id = fields.Many2one('product.product', string="Producto custodia", domain=[('es_custodia', '=', True)])
    product_emision_id = fields.Many2one('product.product', string="Producto emision", domain=[('es_emision', '=', True)])
    partner_id = fields.Many2one('res.partner', string="Emisor", required=True, related="serie_id.partner_id")
    codigo_emisor = fields.Char(string="Código de Emisor", related="serie_id.cod_emisor", store=True)
    currency_id = fields.Many2one('res.currency', string="Moneda",
                                  default=lambda self: self.env.company.currency_id, required=True, related="serie_id.currency_id")
    serie = fields.Char(string="Serie")
    serie_id = fields.Many2one('emisiones.series', string="Serie")
    monto_moneda_original = fields.Monetary(string="Monto en moneda original", related="serie_id.monto_original")
    tc_cierre_mes = fields.Float(string="TC del día")
    monto_pyg = fields.Monetary(string="Monto en PYG")
    instrumento = fields.Selection(string="Instrumento", selection=[(
        'bonos', 'Bonos'), ('acciones', 'Acciones'), ('fondos', 'Fondos')])
    instrumento_serie = fields.Char(string="Instrumento", related="serie_id.instrumento")
    tasa_instrumento = fields.Float(string="Tasa del instrumento", digits=(16, 4), related="serie_id.tasa_instrumento")
    fecha_inicio_colocacion = fields.Date(string="Inicio colocación", related="serie_id.inicio_colocacion")
    fecha_vencimiento = fields.Date(string="Vencimiento", related="serie_id.fecha_vencimiento")
    plazo = fields.Integer(string="Plazo", related="serie_id.plazo")
    fecha_reporte = fields.Date(string="Fecha de reporte")
    dias_reporte = fields.Integer(string="Días de reporte")
    invoice_id = fields.Many2one('account.move', string="Factura", copy=False, readonly=True)
    invoice_ids = fields.Many2many('account.move', string="Facturas")
    state = fields.Selection(string="Estado", selection=[
        ('draft', 'Borrador'), ('confirmado', 'Confirmado'), ('facturado', 'Facturado'),
        ('cancel', 'Cancelado')], default="draft"
    )

    # Custodia
    custodia_tasa_arancel = fields.Float(string="Tasa Arancel Custodia", digits=(16, 4))
    custodia_arancel = fields.Monetary(string="Arancel Custodia")
    custodia_iva = fields.Monetary(string="IVA Custodia")
    custodia_arancel_pyg = fields.Monetary(string="Arancel Custodia en PYG")
    custodia_total = fields.Monetary(string="Total Custodia")

    # Emision
    emision_tasa_arancel = fields.Float(string="Tasa Arancel Emisión", digits=(16, 4))
    emision_arancel = fields.Monetary(string="Arancel Emisión")
    emision_iva = fields.Monetary(string="IVA Emisión")
    emision_arancel_pyg = fields.Monetary(string="Arancel Emisión en PYG")
    emision_total = fields.Monetary(string="Total Emisión")

    total_emision_custodia = fields.Monetary(string="Total Emisión y Custodia")
    total_emision_custodia_pyg = fields.Monetary(string="Total Emisión y Custodia en PYG")

    @api.depends('serie_id')
    @api.onchange('serie_id')
    def computeFechaReporte(self):
        for i in self:
            date = datetime.date.today()
            year = date.year
            fecha_reporte = '31/12/'+ str(year)
            i.fecha_reporte = datetime.datetime.strptime(fecha_reporte, '%d/%m/%Y')

    @api.depends('fecha_reporte','fecha_inicio_colocacion')
    @api.onchange('fecha_reporte','fecha_inicio_colocacion')
    def computeDiasReporte(self):
        for i in self:
            if i.fecha_reporte and i.fecha_inicio_colocacion:
                dif = i.fecha_reporte - i.fecha_inicio_colocacion
                i.dias_reporte = dif.days

    # Convertimos la moneda original a PYG
    @api.onchange('monto_moneda_original', 'currency_id', 'tc_cierre_mes')
    @api.depends('monto_moneda_original', 'currency_id', 'tc_cierre_mes')
    def _onchange_monto_moneda_original(self):
        for record in self:
            # Si la divisa original es PYG, no hacemos nada
            if record.currency_id.name == 'PYG':
                record.monto_pyg = record.monto_moneda_original
            else:
                record.monto_pyg = record.monto_moneda_original * record.tc_cierre_mes

    # Al elegir la moneda original, seteamos el TC
    @api.onchange('currency_id')
    @api.depends('currency_id')
    def _onchange_currency_id(self):
        for record in self:
            try:
                # Obtenemos el TC del mes
                tc = self.env['res.currency.rate'].search([('currency_id', '=', record.currency_id.id)], limit=1)
                record.tc_cierre_mes = tc.inverse_company_rate
            except Exception as e:
                print(e)

    # Obtenemos los días de reporte restando la fecha_reporte con la fecha_colocación
    @api.onchange('fecha_inicio_colocacion', 'fecha_reporte')
    @api.depends('fecha_inicio_colocacion', 'fecha_reporte')
    def _onchange_dias_reporte(self):
        try:
            for record in self:
                record.dias_reporte = (record.fecha_reporte - record.fecha_inicio_colocacion).days
        except Exception as e:
            print(e)

    # Cuando cambia el instrumento
    @api.onchange('instrumento_serie')
    @api.depends('instrumento_serie')
    def _onchange_instrumento(self):
        for record in self:
            # Establecemos el producto para la emisión
            if record.instrumento_serie and 'bono' in record.instrumento_serie.lower():
                producto_emision = self.env['product.product'].search([('es_bono', '=', True)], limit=1)
                record.product_emision_id = producto_emision.id

                producto_custodia = self.env['product.product'].search([('es_custodia', '=', True)], limit=1)
                record.product_custodia_id = producto_custodia.id
            else:
                producto_emision = self.env['product.product'].search(
                    [('es_emision', '=', True), ('es_bono', '=', False)], limit=1)
                record.product_emision_id = producto_emision.id

            self.obtener_arancel_emision()
            self.obtener_arancel_custodia()

    # Calculamos el arancel y los totales
    @api.onchange('plazo', 'dias_reporte', 'monto_pyg', 'instrumento_serie', 'custodia_tasa_arancel', 'emision_tasa_arancel')
    @api.depends('plazo', 'dias_reporte', 'monto_pyg', 'instrumento_serie', 'custodia_tasa_arancel', 'emision_tasa_arancel')
    def _onchange_arancel(self):
        for record in self:
            # Total sin IVA
            record.custodia_arancel = record.monto_moneda_original * (
                record.custodia_tasa_arancel / 365) * record.dias_reporte
            if record.emision_tasa_arancel == 2500000:
                record.emision_arancel = 2500000
            else:
                record.emision_arancel = record.monto_moneda_original * record.emision_tasa_arancel

            # Calculamos el IVA
            record.custodia_iva = record.custodia_arancel * 0.10
            record.emision_iva = record.emision_arancel * 0.10

            # Totales
            record.custodia_total = record.custodia_arancel + record.custodia_iva
            record.emision_total = record.emision_arancel + record.emision_iva

            record.custodia_arancel_pyg = record.custodia_total
            record.emision_arancel_pyg = record.emision_total

            # Si la moneda original es USD, convertimos a PYG
            if record.currency_id.name == 'USD':
                record.custodia_arancel_pyg = record.custodia_total * record.tc_cierre_mes
                record.emision_arancel_pyg = record.emision_total * record.tc_cierre_mes

            record.total_emision_custodia = record.custodia_total + record.emision_total
            record.total_emision_custodia_pyg = record.custodia_arancel_pyg + record.emision_arancel_pyg

    def obtener_arancel_emision(self):
        if self.instrumento_serie and 'bono' in self.instrumento_serie.lower():
            if 90 <= self.plazo < 365:
                self.emision_tasa_arancel = 0.0004
            elif 366 <= self.plazo < 730:
                self.emision_tasa_arancel = 0.0005
            elif self.plazo >= 731:
                self.emision_tasa_arancel = 0.0007

        elif self.instrumento_serie and 'acciones' in self.instrumento_serie.lower():
            if 0 <= self.monto_pyg <= 6500000000:
                self.emision_tasa_arancel = 2500000
            elif self.monto_pyg >= 6500000001:
                self.emision_tasa_arancel = 0.0004

        elif self.instrumento_serie and 'fondos' in self.instrumento_serie.lower():
            if 0 <= self.monto_pyg <= 6500000000:
                self.emision_tasa_arancel = 2500000
            elif 6500000001 <= self.monto_pyg <= 100000000000000:
                self.emision_tasa_arancel = 0.0004
        else:
            self.emision_tasa_arancel = 0.0002

    def obtener_arancel_custodia(self):
        if self.instrumento_serie and 'bono' in self.instrumento_serie.lower():
            self.custodia_tasa_arancel = 0.0001
        else:
            self.custodia_tasa_arancel = 0

    def button_facturar(self):
        view_id = self.env.ref('emisiones_custodia.emisiones_wizard_facturar_form')
        return {
            'name': 'Generar factura',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'emisiones.wizard.facturar',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_emisiones_ids': [(6, 0, self.ids)]}
        }

    def action_facturar(self, journal_id, estado_factura, fecha_factura):
        try:
            emisiones = self
            move_type = 'out_invoice'

            # Obtenemos un listado unico de empresas (partner_id)
            partners = list(set(emisiones.mapped('partner_id')))

            # si alguna emisión no tiene empresa, no se puede facturar
            if not partners:
                raise exceptions.ValidationError('Existen emisiones sin empresa. Favor verificar')

            invoices = []
            for p in partners:
                # Obtenemos las emisiones de la empresa
                _emisiones = emisiones.filtered(lambda x: x.partner_id == p)
                lines = []

                # Verificamos que todas las emisiones tengan la misma moneda
                currency = list(set(_emisiones.mapped('currency_id')))
                if len(currency) > 1:
                    raise exceptions.ValidationError('Existen emisiones con monedas diferentes. Favor verificar')
                else:
                    currency = currency[0]

                # Iteramos por las emisiones para crear las (0, 0, data)s de la factura
                for emision_factura in _emisiones:

                    # Obtenemos la cuenta contable del producto
                    account_id = False
                    if emision_factura.product_custodia_id.property_account_income_id:
                        account_id = emision_factura.product_custodia_id.property_account_income_id.id

                    elif emision_factura.product_custodia_id.categ_id.property_account_income_categ_id:
                        account_id = emision_factura.product_custodia_id.categ_id.property_account_income_categ_id.id

                    elif journal_id.default_account_id:
                        account_id = journal_id.default_account_id.id

                    analytic_account_id = False
                    analytic_tag_ids = False
                    # TODO: Verificar si se debe usar el analytic account y tags de la emisión
                    # if emision_factura.analytic_account_id:
                    #     analytic_account_id = emision_factura.analytic_account_id.id
                    # if emision_factura.analytic_tag_ids:
                    #     analytic_tag_ids = [(6, 0, emision_factura.analytic_tag_ids.ids)]

                    if not account_id:
                        raise exceptions.ValidationError(
                            'No está definida la cuenta de contable del Producto, Categoría de producto o del Diario. Favor verificar')

                    # Agregamos el producto de custodia
                    if emision_factura.product_custodia_id:
                        data = {
                            'product_id': emision_factura.product_custodia_id.id,
                            'name': emision_factura.product_custodia_id.display_name,
                            'quantity': 1,
                            'price_unit': emision_factura.custodia_total,
                            'tax_ids': [(6, 0, emision_factura.product_custodia_id.taxes_id.ids)],
                            'account_id': account_id,
                            'analytic_account_id': analytic_account_id,
                            'analytic_tag_ids': analytic_tag_ids
                        }
                        lines.append((0, 0, data))

                    # Agregamos el producto de emision
                    if emision_factura.product_emision_id:
                        data = {
                            'product_id': emision_factura.product_emision_id.id,
                            'name': emision_factura.product_emision_id.display_name,
                            'quantity': 1,
                            'price_unit': emision_factura.emision_total,
                            'tax_ids': [(6, 0, emision_factura.product_emision_id.taxes_id.ids)],
                            'account_id': account_id,
                            'analytic_account_id': analytic_account_id,
                            'analytic_tag_ids': analytic_tag_ids
                        }
                        lines.append((0, 0, data))

                invoice = {
                    'journal_id': journal_id.id,
                    'partner_id': p.id,
                    'invoice_date': fecha_factura or datetime.date.today(),
                    'invoice_date_due': datetime.date.today(),
                    'currency_id': currency.id,
                    'move_type': move_type,
                    'invoice_line_ids': lines
                }
                invoice_id = self.env['account.move'].create(invoice)

                if invoice_id:
                    _emisiones.write({'invoice_ids': [(4, invoice_id.id, 0)]})
                    if estado_factura == 'posted':
                        invoice_id.action_post()

                    invoices.append(invoice_id.id)
            return invoices
        except Exception as e:
            print(e)
            raise exceptions.ValidationError(e)

    def button_borrador(self):
        for i in self:
            if i.invoice_ids and i.invoice_ids.filtered(lambda x: x.state == 'posted'):
                raise exceptions.ValidationError(
                    'No se puede cambiar a borrador cuotas facturadas')
            if i.state != 'cancel':
                raise exceptions.ValidationError(
                    'No se puede cambiar a borrador cuotas no canceladas')

        self.write({'state': 'draft'})

    def button_confirmar(self):
        for i in self:
            if i.state != 'draft':
                raise exceptions.ValidationError('No se puede confirmar emisiones que no estén en borrador')
        self.write({'state': 'confirmado'})
