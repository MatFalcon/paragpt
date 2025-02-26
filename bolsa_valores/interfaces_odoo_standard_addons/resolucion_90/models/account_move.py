from odoo import models, fields, api, exceptions
import re


class AccountMove(models.Model):
    _inherit = 'account.move'

    res90_tipo_identificacion = fields.Selection([('11', 'RUC'), ('12', 'Cédula de identidad'), ('13', 'Pasaporte'), (
        '14', 'Cédula extranjero'), ('15', 'Sin nombre'), ('16', 'Diplomático'), ('17', 'Identificación tributaria')],
                                                 default='11')

    res90_tipo_comprobante = fields.Selection([('101', 'Autofactura'),
                                               ('102', 'Boleta de Transporte Público de Pasajeros'),
                                               ('103', 'Boleta de Venta'),
                                               ('104', 'Boleta Resimple'),
                                               ('105', 'Boletos de Loterías, Juegos de Azar'),
                                               ('106', 'Boleto o ticket de Transporte aéreo'),
                                               ('107', 'Despacho de importación'),
                                               ('108', 'Entrada a espectáculos públicos'),
                                               ('109', 'Factura'),
                                               ('110', 'Nota de crédito'),
                                               ('111', 'Nota de débito'),
                                               ('112', 'Ticket de máquina registradora'),
                                               ('201', 'Comprobante de egresos por compras a crédito'),
                                               ('202', 'Comprobante del exterior legalizado'),
                                               ('203', 'Comprobante de ingreso por ventas a crédito'),
                                               ('204',
                                                'Comprobante de ingreso de Entidades Públicas, Religiosas o de Beneficio Público'),
                                               ('205', 'Extracto de cuenta - Billetaje electrónico'),
                                               ('206', 'Extracto de cuenta - IPS'),
                                               ('207', 'Extracto de cuenta - TC/TD'),
                                               ('208', 'Liquidación de Salario'),
                                               ('209', 'Otros comprobantes de egresos'),
                                               ('210', 'Otros comprobantes de ingresos'),
                                               ('211', 'Transferencias o giros bancarios / Boleta de depósito'),
                                               ])
    res90_nro_timbrado = fields.Char(string='Nro. de timbrado')
    res90_imputa_iva = fields.Boolean(string="Imputa IVA", default=True)
    res90_imputa_ire = fields.Boolean(string="Imputa IRE")
    res90_imputa_irp_rsp = fields.Boolean(string="Imputa IRP/RSP")
    res90_no_imputa = fields.Boolean(string="No imputa", default=False)
    res90_nro_comprobante_asociado = fields.Char(string="Nro. de comprobante asociado")
    res90_timbrado_comprobante_asociado = fields.Char(string="Nro. de timbrado de comprobante asociado")
    excluir_res90 = fields.Boolean(string="Excluir de Resolucion 90",
                                   help="Los registros de este diario no serán incluídos en la resolucion 90")

    @api.onchange('company_id')
    @api.depends('company_id')
    def onchangeCompany(self):
        for i in self:
            if i.company_id.res90_imputa_irp_rsp_defecto:
                i.res90_imputa_irp_rsp = True

    @api.onchange('journal_id')
    @api.depends('journal_id')
    def asignar_tipo_comprobante(self):
        for i in self:
            if i.journal_id:
                if i.journal_id.res90_tipo_comprobante:
                    i.res90_tipo_comprobante = i.journal_id.res90_tipo_comprobante
                elif i.move_type in ['out_invoice', 'in_invoice']:
                    i.res90_tipo_comprobante = '109'
                elif i.move_type in ['out_refund', 'in_refund']:
                    i.res90_tipo_comprobante = '110'
                else:
                    i.res90_tipo_comprobante = None

    @api.onchange('partner_id')
    @api.depends('partner_id')
    def asignar_tipo_identificacion(self):
        for i in self:
            if i.partner_id:
                if not i.partner_id.vat:
                    i.res90_tipo_identificacion = '15'
                else:
                    pattern = "^[0-9]+-[0-9]$"
                    if re.match(pattern, i.partner_id.vat) and i.partner_id.vat != '44444401-7':
                        i.res90_tipo_identificacion = '11'
                    elif re.match(pattern, i.partner_id.vat) and i.partner_id.vat == '44444401-7':
                        i.res90_tipo_identificacion = '15'
                    else:
                        pattern = "^[0-9]+$"
                        if re.match(pattern, self.partner_id.vat):
                            i.res90_tipo_identificacion = '12'
                        else:
                            i.res90_tipo_identificacion = '15'

    def get_tipo_identificacion(self):
        if self.res90_tipo_identificacion:
            return int(self.res90_tipo_identificacion)
        return 15

    def get_identificacion(self):
        identificacion = self.partner_id.vat

        if identificacion and len(identificacion.split('-')) > 1:
            identificacion = identificacion.split('-')[0]

        return identificacion if self.partner_id.vat else '44444401'

    def get_nombre_partner(self):
        return self.partner_id.name

    def get_tipo_comprobante(self):
        if self.res90_tipo_comprobante:
            return int(self.res90_tipo_comprobante)
        elif self.move_type in ['in_invoice', 'out_invoice']:
            return 109
        elif self.move_type in ['in_refund', 'out_refund']:
            return 110
        else:
            return ''

    def get_fecha_comprobante(self):
        return self.date.strftime('%d/%m/%Y')

    def get_timbrado(self):
        if self.res90_nro_timbrado:
            try:
                return int(self.res90_nro_timbrado)
            except:
                raise exceptions.ValidationError(
                    "El valor " + self.res90_nro_timbrado + " en el campo de Nro Timbrado del asiento " + self.name + " no puede ser procesado, por favor verificar si está correcto")
        return 0

    def get_numero_comprobante(self):
        if self.move_type in ['out_invoice', 'out_refund']:
            return self.name
        elif self.move_type in ['in_invoice', 'in_refund']:
            return self.ref
        else:
            return ''

    def get_monto10(self):
        monto10 = sum(self.invoice_line_ids.filtered(lambda x: 10 in x.tax_ids.mapped('amount')).mapped('price_total'))
        if self.currency_id != self.env.company.currency_id:
            balance = abs(sum(self.invoice_line_ids.filtered(lambda x:x.currency_id == self.currency_id).mapped('balance')))
            amount_currency = abs(sum(self.invoice_line_ids.filtered(lambda x:x.currency_id == self.currency_id).mapped('amount_currency')))
            if balance > 0 and amount_currency > 0:
                currency_rate = balance / amount_currency
            else:
                currency_rate = 1
            monto10 = monto10 * currency_rate
        return round(monto10)

    def get_monto5(self):
        monto5 = sum(self.invoice_line_ids.filtered(lambda x: 5 in x.tax_ids.mapped('amount')).mapped('price_total'))
        if self.currency_id != self.env.company.currency_id:
            balance = abs(sum(self.invoice_line_ids.filtered(lambda x:x.currency_id == self.currency_id).mapped('balance')))
            amount_currency = abs(sum(self.invoice_line_ids.filtered(lambda x:x.currency_id == self.currency_id).mapped('amount_currency')))
            if balance > 0 and amount_currency > 0:
                currency_rate = balance / amount_currency
            else:
                currency_rate = 1
            monto5 = monto5 * currency_rate
        return round(monto5)

    def get_monto_exento(self):
        monto0 = sum(self.invoice_line_ids.filtered(lambda x: not x.tax_ids or 0 in x.tax_ids.mapped('amount')).mapped('price_total'))
        if self.currency_id != self.env.company.currency_id:
            balance = abs(sum(self.invoice_line_ids.filtered(lambda x:x.currency_id == self.currency_id).mapped('balance')))
            amount_currency = abs(sum(self.invoice_line_ids.filtered(lambda x:x.currency_id == self.currency_id).mapped('amount_currency')))
            if balance > 0 and amount_currency > 0:
                currency_rate = balance / amount_currency
            else:
                currency_rate = 1
            monto0 = monto0 * currency_rate
        return round(monto0)

    def get_monto_total(self):
        monto = abs(sum(self.invoice_line_ids.mapped('price_total')))
        if self.currency_id != self.env.company.currency_id:
            balance = abs(sum(self.invoice_line_ids.filtered(lambda x:x.currency_id == self.currency_id).mapped('balance')))
            amount_currency = abs(sum(self.invoice_line_ids.filtered(lambda x:x.currency_id == self.currency_id).mapped('amount_currency')))
            if balance > 0 and amount_currency > 0:
                currency_rate = balance / amount_currency
            else:
                currency_rate = 1
            monto = monto * currency_rate
        return round(monto)

    def get_condicion_venta(self):
        if self.invoice_date_due > self.invoice_date:
            return 2
        return 1

    def get_operacion_moneda_extranjera(self):
        if self.currency_id and self.currency_id.name == 'PYG':
            return 'N'
        elif self.currency_id and self.currency_id.name != 'PYG':
            return 'S'
        else:
            return 'N'

    def get_imputa_iva(self):
        if self.get_imputa_iva:
            return 'S'
        return 'N'

    def get_imputa_ire(self):
        if self.res90_imputa_ire:
            return 'S'
        return 'N'

    def get_imputa_irp_rsp(self):
        if self.res90_imputa_irp_rsp:
            return 'S'
        return 'N'

    def get_no_imputa(self):
        if self.res90_no_imputa:
            return 'S'
        return 'N'

    def get_nro_comprobante_asociado(self):
        if self.res90_nro_comprobante_asociado:
            return self.res90_nro_comprobante_asociado
        return ''

    def get_timbrado_comprobante_asociado(self):
        if self.res90_timbrado_comprobante_asociado:
            return self.res90_timbrado_comprobante_asociado
        return ''

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for i in self:
            if i.move_type in ['out_invoice', 'out_refund']:
                tim = i.journal_id.timbrados_ids.filtered(lambda x: x.tipo_documento == i.move_type)
                if len(tim) > 1:
                    raise exceptions.ValidationError('Tiene mas de un timbrado para este tipo de factura')
                elif len(tim) == 1:
                    i.write({'res90_nro_timbrado': tim.name})
                    # i.write({'res90_nro_timbrado':i.timbrado})
            elif i.move_type in ['in_invoice', 'in_refund']:
                i.write({'res90_nro_timbrado': i.timbrado_proveedor})
        return res

    # Funcion ejecutada por una accion planificada para rellenar campos del rg90
    @api.model
    def rg90_remision_campos(self):
        f_remision_venta = self.env['account.move'].search(
            [('move_type', '=', 'out_refund'), ('reversed_entry_id', '!=', False)])
        for fac in f_remision_venta:
            try:
                timb = ''
                if fac.reversed_entry_id.journal_id and fac.reversed_entry_id.journal_id.timbrados_ids:
                    timb = fac.reversed_entry_id.journal_id.timbrados_ids[0].name
                if not fac.reversed_entry_id.res90_nro_comprobante_asociado or not fac.reversed_entry_id.res90_timbrado_comprobante_asociado:
                    fac.reversed_entry_id.sudo().write({
                        'res90_nro_comprobante_asociado': fac.name,
                        'res90_timbrado_comprobante_asociado': timb
                    })
                timb = ''
                if fac.journal_id and fac.journal_id.timbrados_ids:
                    timb = fac.journal_id.timbrados_ids[0].name

                if not fac.res90_nro_comprobante_asociado or not fac.res90_timbrado_comprobante_asociado:
                    fac.sudo().write({
                        'res90_nro_comprobante_asociado': fac.reversed_entry_id.name or '',
                        'res90_timbrado_comprobante_asociado': timb
                    })
            except Exception as e:
                print(e)
                continue

        f_remision_compra = self.env['account.move'].search(
            [('move_type', '=', 'in_refund'), ('reversed_entry_id', '!=', False)])
        for fac in f_remision_compra:
            try:
                timb = ''
                if fac.reversed_entry_id.timbrado_id:
                    timb = fac.reversed_entry_id.timbrado_id.name

                if not fac.reversed_entry_id.res90_nro_comprobante_asociado or not fac.reversed_entry_id.res90_timbrado_comprobante_asociado:
                    fac.reversed_entry_id.sudo().write({
                        'res90_nro_comprobante_asociado': fac.name,
                        'res90_timbrado_comprobante_asociado': timb
                    })
                timb = ''
                if fac.timbrado_id:
                    timb = fac.timbrado_id.name

                if not fac.res90_nro_comprobante_asociado or not fac.res90_timbrado_comprobante_asociado:
                    fac.sudo().write({
                        'res90_nro_comprobante_asociado': fac.reversed_entry_id.name,
                        'res90_timbrado_comprobante_asociado': timb
                    })
            except Exception as e:
                print(e)
                continue
