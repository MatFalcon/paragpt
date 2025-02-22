# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, _
import datetime
import requests
import json
from msal import PublicClientApplication
import logging
_logger = logging.getLogger(__name__)


class CustodiaFisica(models.Model):
    _name = 'custodia_fisica.custodia_fisica'
    _description = 'custodia_fisica.custodia_fisica'

    name = fields.Char(string="Nombre", default=lambda self: _('New'))
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one(
        'res.currency', string="Moneda", default=lambda self: self.env.user.company_id.currency_id)
    arancel_currency_id = fields.Many2one(
        'res.currency', string="Moneda de arancel")
    partner_id = fields.Many2one('res.partner', string="Cliente")
    cantidad_custodiada = fields.Float(string="Cantidad Custodiada")
    arancel_cantidad = fields.Monetary(
        string="Arancel por cantidad custodiada")
    monto_custodiado = fields.Monetary(
        string="Importe custodiado", currency_field="arancel_currency_id")
    arancel_monto = fields.Monetary(string="Arancel por monto custodiado")
    arancel_total = fields.Monetary(string="Arancel Total")
    descuento = fields.Float(string="Descuento")
    custodia_total = fields.Monetary(string="Custodia a facturar")
    invoice_id = fields.Many2one('account.move', string='Factura')
    fecha_inicio = fields.Date(string="Fecha Inicio")
    fecha_fin = fields.Date(string="Fecha Fin")
    line_ids = fields.One2many(
        'custodia_fisica.custodia_fisica_line', 'custodia_id')
    state = fields.Selection(string="Estado", selection=[
        ('draft', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('facturado', 'Facturado'),
        ('cancel', 'Cancelado')], default="draft"
    )
    total_iva = fields.Monetary(
        string="Total IVA", compute="_get_total_iva", store=True)
    total_gravada = fields.Monetary(
        string="Total gravada", compute="_get_total_iva", store=True)

    @api.onchange('descuento')
    @api.depends('descuento', 'arancel_total')
    def _descuento_onchange(self):
        for record in self:
            record.custodia_total = record.arancel_total - \
                ((record.arancel_total * record.descuento) / 100)
            record._get_total_iva()

    @api.depends('custodia_total')
    def _get_total_iva(self):
        for record in self:
            iva = record.custodia_total / 11
            record.total_iva = iva
            # record.total_gravada = record.custodia_total * 1.1
            record.total_gravada = record.custodia_total - iva

    def unlink(self, force=False):
        if any(self.filtered(lambda x: x.state != 'draft')):
            raise exceptions.ValidationError(
                'Solo se pueden borrar custodias en borrador')
        super(CustodiaFisica, self).unlink()

    @ api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.partner_id.name or _('New')
        res = super(CustodiaFisica, self).create(vals)
        return res

    def button_facturar(self):
        if any(self.filtered(lambda x: x.state != 'confirmado')):
            raise exceptions.ValidationError(
                'No se pueden facturar custodias que no estén confirmadas')

        view_id = self.env.ref(
            'custodia_fisica.custodia_fisica_wizard_facturar_form')
        return {
            'name': 'Generar factura',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'custodia_fisica.wizard.facturar',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_custodia_fisica_ids': [(6, 0, self.ids)]}
        }

    def action_facturar(self, journal_id, estado_factura, fecha_factura):
        invoices = []
        facturadas = self.mapped('invoice_id')
        if facturadas:
            raise exceptions.ValidationError(
                'Existen custodias ya facturadas. Favor verificar')

        for record in self:
            Partner = record.partner_id
            Currency = record.company_id.currency_id
            Product = self.env['product.product'].search(
                [('es_custodia_fisica', '=', True)])

            if not Partner:
                raise exceptions.ValidationError(
                    'Existen custodias sin cliente')

            if not Product:
                raise exceptions.ValidationError(
                    'No existe un producto destinado a custodias físicas. Favor verificar')

            if len(Product) > 1:
                raise exceptions.ValidationError(
                    'Existe mas de un producto destinado a custodias físicas. Favor verificar')

            account_id = False
            if Product.property_account_income_id:
                account_id = Product.property_account_income_id.id
            elif Product.categ_id.property_account_income_categ_id:
                account_id = Product.categ_id.property_account_income_categ_id.id
            elif journal_id.default_account_id:
                account_id = journal_id.default_account_id.id
            # elif cuota.tipo_cuota=='purchase':
            #     if cuota.product_id.property_account_expense_id:
            #         account_id = cuota.product_id.property_account_expense_id.id
            #     elif cuota.product_id.categ_id.property_account_expense_categ_id:
            #         account_id = cuota.product_id.categ_id.property_account_expense_categ_id.id
            #     elif journal_id.default_account_id:
            #         account_id = journal_id.default_account_id.id

            # analytic_account_id = False
            # analytic_tag_ids = False
            # if record.analytic_account_id:
            #     analytic_account_id = record.analytic_account_id.id
            # if record.analytic_tag_ids:
            #     analytic_tag_ids = [
            #         (6, 0, record.analytic_tag_ids.ids)]

            if not account_id:
                raise exceptions.ValidationError(
                    'No está definida la cuenta de contable del Producto, Categoría de producto o del Diario. Favor verificar')

            invoice_id = self.env['account.move'].create(
                {
                    'journal_id': journal_id.id,
                    'partner_id': Partner.id,
                    'invoice_date': fecha_factura or datetime.date.today(),
                    'invoice_date_due': fecha_factura or datetime.date.today(),
                    'currency_id': Currency.id,
                    'move_type': 'out_invoice',
                    'invoice_line_ids': [(0, 0, {
                        'product_id': Product.id,
                        'name': Product.display_name,
                        'quantity': 1,
                        'price_unit': record.custodia_total,
                        'tax_ids': [(6, 0, Product.taxes_id.ids)],
                        'account_id': account_id
                    })]
                }
            )
            if invoice_id:
                record.write({
                    'invoice_id': invoice_id.id,
                    'state': 'facturado'
                })
                invoices.append(invoice_id.id)
        return invoices

    def action_draft(self):
        for record in self:
            if record.invoice_id:
                raise exceptions.ValidationError(
                    'No se puede cambiar a borrador custodias físicas facturadas')
            if record.state != 'cancel':
                raise exceptions.ValidationError(
                    'No se puede cambiar a borrador custodias físicas no canceladas')

        self.write({'state': 'draft'})

    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise exceptions.ValidationError(
                    'No se pueden confirmar líneas de custodias que no estén en borrador')
        self.write({'state': 'confirmado'})

    def action_cancelar(self):
        for record in self:
            if record.invoice_id:
                raise exceptions.ValidationError(
                    'No se pueden cancelar custodias que estén facturadas')
        self.write({'state': 'cancel'})


class CustodiaFisicaLine(models.Model):
    _name = 'custodia_fisica.custodia_fisica_line'
    _description = 'custodia_fisica.custodia_fisica_line'

    custodia_id = fields.Many2one('custodia_fisica.custodia_fisica')
    company_id = fields.Many2one(
        'res.company', string="Compañia", default=lambda self: self.env.user.company_id)
    partner_id = fields.Many2one('res.partner', string="Cliente")
    tipo_titulo = fields.Many2one('product.product', string="Tipo de Título")
    cantidad = fields.Float(string="Cantidad", default="1.0")
    valor_nominal = fields.Monetary(string="Valor Nominal")
    currency_id = fields.Many2one('res.currency', string="Moneda")
    fecha_emision = fields.Date(string="Fecha de emisión")
    fecha_vencimiento = fields.Date(string="Fecha de vencimiento")

    def unlink(self, force=False):
        if self.custodia_id:
            raise exceptions.ValidationError(
                'No se pueden borrar líneas de custodias custodias que ya fueron facturadas')
        super(CustodiaFisicaLine, self).unlink()

    def obtener_session_dataverse(self):
        Envy = self.env['ir.config_parameter'].sudo()
        config = {
            "authority": Envy.get_param("geene_authority_url"),
            "client_id": Envy.get_param("geene_cleint_id"),
            "username": Envy.get_param("geene_username"),
            "password": Envy.get_param("geene_password"),
            "scope": [Envy.get_param("geene_scope")],
            "endpoint": Envy.get_param("geene_enpoint")
        }

        result = None
        try:
            app = PublicClientApplication(
                config["client_id"],
                authority=config["authority"])
        except Exception as e:
            _logger.info(str(e))

        accounts = app.get_accounts(username=config["username"])
        if accounts:
            result = app.acquire_token_silent(
                config["scope"], account=accounts[0])

        if not result:
            try:
                result = app.acquire_token_by_username_password(
                    config["username"], config["password"], scopes=config["scope"])
            except Exception as e:
                _logger.info(str(e))

        if "access_token" in result:
            _logger.info("access_token found")
            session = requests.Session()
            session.headers.update({"Content-Type": "application/json"})
            session.headers.update(
                {"Authorization": "Bearer " + str(result['access_token'])})
            session.headers.update({"OData-MaxVersion": "4.0"})
            session.headers.update({"OData-Version": "4.0"})
            return session
        else:
            _logger.info("no access_token")
            if 65001 in result.get("error_codes", []):
                # Utilizado para autorizar desde un link
                if self.env.user._is_admin():
                    raise exceptions.UserError(
                        "Visit this to consent: " + str(app.get_authorization_request_url(scopes=config['scope'])))
                else:
                    raise exceptions.UserError(
                        "Error de validadicon en la API")

            if self.env.user._is_admin():
                _logger.info(result['error_description'])
                raise exceptions.UserError(result['error_description'])
            else:
                raise exceptions.UserError(
                    "Error de validadicon en la API")

    def get_vals_api(self, next_link=None):
        # codigo de las monedas en la api
        # c43417e1-a60a-ec11-b6e6-00224808dbe7 -> PYG
        # 8f4e8bdf-6802-ec11-94ee-000d3a59bcc4 -> UDS
        session = self.obtener_session_dataverse()

        URL = self.env['ir.config_parameter'].sudo().get_param("geene_enpoint")

        params = {"$select": "new_instrumentoid,_new_entidaddepositante_value,new_tipodetitulo,_transactioncurrencyid_value,new_valornominal,new_fechaingresoegreso,statuscode,exchangerate",
                  "$filter": "statuscode eq 100000000"}

        if not next_link:
            response = session.get(URL, params=params, timeout=10)
        else:
            response = session.get(next_link, timeout=10)

        _logger.info("Api response {0}".format(response.status_code))
        # nextlink = response.json()['@odata.nextLink']
        values = response.json()['value']

        #elimiando las importaciones anteriores
        # self.env['custodia_fisica.import_lines'].search([('id','!=',False)]).unlink()
        # self.env['custodia_fisica.import_lines'].search([("procesado", "=", False)]).unlink()

        for value in values:
            currency_id = 2
            fecha_ingreso = None

            # consultar si existe la lienea a importar para evitar duplicados
            custodias_import = self.env["custodia_fisica.import_lines"].search([
                ("new_instrumentoid", "=", value["new_instrumentoid"])
            ])

            if not custodias_import:
                partner = self.env["res.partner"].search(
                    [("geene_api_pk", "=", value["_new_entidaddepositante_value"])])
                product = self.env["product.product"].search(
                    [("geene_api_pk", "=", value["new_tipodetitulo"])])

                if value['new_fechaingresoegreso']:
                    fecha_ingreso = datetime.datetime.strptime(
                        str(value['new_fechaingresoegreso'])[:10], '%Y-%m-%d').date()

                if value['_transactioncurrencyid_value'] == "c43417e1-a60a-ec11-b6e6-00224808dbe7":
                    currency_id = 155

                if len(partner) == 1 and len(product) == 1:
                    self.env["custodia_fisica.import_lines"].create({
                        "new_instrumentoid": value['new_instrumentoid'],
                        "new_entidaddepositante_value": partner.id,
                        "new_tipodetitulo": product.id,
                        "transactioncurrencyid_value": value['_transactioncurrencyid_value'],
                        "new_valornominal": value['new_valornominal'],
                        "new_fechaingresoegreso": fecha_ingreso,
                        "exchangerate": value["exchangerate"],
                        "currency_id": currency_id,
                    })
                    # self.env.cr.commit()
                    # self.create_lineas_custodia()

        if "@odata.nextLink" in response.json():
            self.get_vals_api(response.json()['@odata.nextLink'])

    def create_lineas_custodia(self, add_import=True):
        # vaciar impotaciónes para volver a importar debido a variaciones de estados en la api
        self.env['custodia_fisica.import_lines'].search([('id','!=',False)]).unlink()
        #imporat las lineas desde la api
        if add_import:
            self.get_vals_api()
        
        #elimina custodia no agrupadas
        self.search([('custodia_id','=',False)]).unlink()

        # Seleccionar y agrupar las lineas para poder crear las custodias con su encabezado
        # loop para USD
        raw_lines_usd = self.env["custodia_fisica.import_lines"].search([
            ("procesado", "=", False),
            # ("new_fechaingresoegreso", "<", fields.Date.today()),
            ("currency_id", "=", 2),
        ])
        for entidad_depo in raw_lines_usd.mapped('new_entidaddepositante_value'):
            for tipo_titulo in raw_lines_usd.filtered(lambda x: x.new_entidaddepositante_value == entidad_depo).mapped('new_tipodetitulo'):
                lines = raw_lines_usd.filtered(lambda x: x.new_entidaddepositante_value ==
                                               entidad_depo and x.new_tipodetitulo == tipo_titulo)
                # for fecha in set(raw_lines_usd.filtered(lambda x: x.new_entidaddepositante_value == entidad_depo and x.new_tipodetitulo == tipo_titulo).mapped('new_fechaingresoegreso')):
                #     lines = raw_lines_usd.filtered(lambda x: x.new_entidaddepositante_value ==
                #                                    entidad_depo and x.new_tipodetitulo == tipo_titulo and x.new_fechaingresoegreso == fecha)
                self.create({
                    "partner_id": entidad_depo.id,
                    "tipo_titulo": tipo_titulo.id,
                    "cantidad": len(lines),
                    "valor_nominal": sum(lines.mapped('new_valornominal')),
                    "currency_id": 2,
                    # "fecha_emision": fecha
                    "fecha_emision": fields.Date.today()
                })
                lines.update({'procesado': True})

        # loop para PYG
        raw_lines_pyg = self.env["custodia_fisica.import_lines"].search([
            ("procesado", "=", False),
            # ("new_fechaingresoegreso", "<", fields.Date.today()),
            ("currency_id", "=", 155),
        ])

        for entidad_depo in raw_lines_pyg.mapped('new_entidaddepositante_value'):
            for tipo_titulo in raw_lines_pyg.filtered(lambda x: x.new_entidaddepositante_value == entidad_depo).mapped('new_tipodetitulo'):
                lines = raw_lines_pyg.filtered(lambda x: x.new_entidaddepositante_value ==
                                               entidad_depo and x.new_tipodetitulo == tipo_titulo)
                # for fecha in set(raw_lines_pyg.filtered(lambda x: x.new_entidaddepositante_value == entidad_depo and x.new_tipodetitulo == tipo_titulo).mapped('new_fechaingresoegreso')):
                #     lines = raw_lines_pyg.filtered(lambda x: x.new_entidaddepositante_value ==
                #                                    entidad_depo and x.new_tipodetitulo == tipo_titulo and x.new_fechaingresoegreso == fecha)
                self.create({
                    "partner_id": entidad_depo.id,
                    "tipo_titulo": tipo_titulo.id,
                    "cantidad": len(lines),
                    "valor_nominal": sum(lines.mapped('new_valornominal')),
                    "currency_id": 155,
                    # "fecha_emision": fecha
                    "fecha_emision": fields.Date.today()
                })
                lines.update({'procesado': True})

    def action_crear_custodia(self):
        "Agrega encabezado para las líneas de fatura física"

        Arancel = self.env['custodia_fisica.aranceles_monto'].search([
            ("activo", "=", True),
            ("predeter", "=", True)
        ])
        if len(Arancel) > 1:
            raise exceptions.ValidationError(
                'Existe más de un arancel configurado como predeterminado. Favor verificar')

        procesados = list(set(self.mapped('custodia_id')))
        if procesados:
            raise exceptions.ValidationError(
                'Ya existen líneas procesadas. Favor verificar')

        custodias = []
        for partner in self.mapped('partner_id'):
            _arancel_monto = 0
            _arancel_cantidad = 0
            _monto_custodiado = 0

            _cantidad_custodiada = sum(self.filtered(
                lambda x: x.tipo_titulo.geene_api_pk != "100000001" and x.partner_id == partner).mapped('cantidad'))

            _arancel_cantidad += self._total_arancel_cantidad(
                partner, _cantidad_custodiada)

            for record in self.filtered(lambda x: x.partner_id == partner):
                # caso de moneda diferente conviernte GS del record al USD del arancel
                # toma la ultima cotizacion no usa la fecha de la linea de custodia
                if record.currency_id != Arancel.currency_id:
                    # _monto_custodiado += record.currency_id._convert(
                    #     _monto_custodiado, Arancel.currency_id, record.company_id, record.fecha_emision)

                    _monto_custodiado += record.currency_id._convert(
                        record.valor_nominal, Arancel.currency_id, record.company_id, fields.Date.today())
                elif record.currency_id == Arancel.currency_id:
                    _monto_custodiado += record.valor_nominal

            _arancel_monto = self._total_arancel_monto(
                partner, _monto_custodiado)

            custodia = self.env['custodia_fisica.custodia_fisica'].create({
                'name': partner.name,
                'partner_id': partner.id,
                'cantidad_custodiada': _cantidad_custodiada,
                'arancel_cantidad': _arancel_cantidad,
                'monto_custodiado': _monto_custodiado,
                'arancel_currency_id': Arancel.currency_id.id,
                'arancel_monto': _arancel_monto,
                'arancel_total': _arancel_cantidad + _arancel_monto,
                'descuento': 0,  # desucento se define manualmente
                'custodia_total': _arancel_cantidad + _arancel_monto,
                'fecha_inicio': min(r.fecha_emision for r in self),
                'fecha_fin': max(r.fecha_vencimiento for r in self),
                'line_ids': self.filtered(lambda x: x.partner_id == partner)
            })
            custodias.append(custodia.id)

        return custodias

    def _total_arancel_cantidad(self, partner, cant):
        """
        Obtener el valor correspondiente de jornales por cantidad de líneas seleccionadas
        :param cant: cantidades para tener rango en a lista de aranceles
        :return total_arancel: total de arancel en PYG
        """
        jornal = self.env['mantenimiento_registro.jornal_mantenimiento'].search([
            ('activo', '=', True)
        ])
        total_arancel = 0
        if not partner.arancel_cantidad_id:
            arancel_cantidad = self.env['custodia_fisica.aranceles_cantidad'].search([
                ("activo", "=", True),
                ("predeter", "=", True)
            ])
            if len(arancel_cantidad) > 1:
                raise exceptions.ValidationError(
                    'Existe más de un arancel configurado como predeterminado. Favor verificar')
            else:
                linea_arancel = arancel_cantidad.line_ids.filtered(
                    lambda x: cant >= x.cantidad_desde and cant <= x.cantidad_hasta
                )
                total_arancel = linea_arancel.jornales * jornal.monto

        else:
            arancel_cantidad = partner.arancel_cantidad_id
            linea_arancel = arancel_cantidad.line_ids.filtered(
                lambda x: cant >= x.cantidad_desde and cant <= x.cantidad_hasta
            )
            total_arancel = linea_arancel.jornales * jornal.monto

        return total_arancel

    def _total_arancel_monto(self, partner, monto):
        """
        Obtener la cantidad de jornales fijados en los aranceles por monto
        :param monto: valor en USD
        :return total_arancel: valor en PYG
        """
        jornal = self.env['mantenimiento_registro.jornal_mantenimiento'].search([
            ('activo', '=', True)
        ])
        total_arancel = 0
        if not partner.arancel_monto_id:
            arancel_monto = self.env['custodia_fisica.aranceles_monto'].search([
                ("activo", "=", True),
                ("predeter", "=", True)
            ])
            if len(arancel_monto) > 1:
                raise exceptions.ValidationError(
                    'Existe más de un arancel configurado como predeterminado. Favor verificar')
            else:
                # tener en cuenta la moneda del arancel:
                # FIXED: lienas de custodia siempre van a ser en USD
                # if arancel_monto.currency_id != self.company_id.currency_id:
                #     _monto = self.company_id.currency_id._convert(
                #         monto, arancel_monto.currency_id, self.company_id, self.fecha_emision)
                # else:
                #     _monto = monto

                linea_arancel = arancel_monto.line_ids.filtered(
                    lambda x: x.monto_desde <= monto and x.monto_hasta >= monto
                )
                total_arancel = linea_arancel.jornales * jornal.monto

        else:
            arancel_monto = partner.arancel_monto_id

            # tener en cuenta la moneda del arancel
            # FIXED: lienas de custodia siempre van a ser en USD
            # if arancel_monto.currency_id != self.company_id.currency_id:
            #     _monto = self.company_id.currency_id._convert(
            #         monto, arancel_monto.currency_id, self.company_id, self.fecha_emision)
            # else:
            #     _monto = monto

            linea_arancel = arancel_monto.line_ids.filtered(
                lambda x: x.monto_desde <= monto and x.monto_hasta >= monto
            )
            total_arancel = linea_arancel.jornales * jornal.monto

        return total_arancel

    def button_crear_custodia(self):
        view_id = self.env.ref(
            'custodia_fisica.crear_custodia_wizard_form')
        return {
            'name': 'Generar Custodia',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'custodia_fisica.wizard.crear_custodias',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_custodia_fisica_line_ids': [(6, 0, self.ids)]}
        }


class CustodiaFisicaImportLines(models.Model):
    _name = 'custodia_fisica.import_lines'
    _description = 'custodia_fisica.import_lines'

    # se borra todo para volver a importar
    # lineas de custodia sin procesar se borran cada mes
    new_instrumentoid = fields.Char()
    new_entidaddepositante_value = fields.Many2one('res.partner')
    new_tipodetitulo = fields.Many2one('product.product')
    transactioncurrencyid_value = fields.Char()
    new_valornominal = fields.Float()
    new_cantidad = fields.Float(default=1.0)
    new_fechaingresoegreso = fields.Date()
    exchangerate = fields.Char()
    procesado = fields.Boolean(default=False)
    currency_id = fields.Many2one('res.currency')

    # codigo de las monedas en la api
    # c43417e1-a60a-ec11-b6e6-00224808dbe7 -> PYG
    # 8f4e8bdf-6802-ec11-94ee-000d3a59bcc4 -> UDS
