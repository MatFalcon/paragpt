import datetime

from odoo import models, fields, api, exceptions


class FacturasCuotaSen(models.Model):
    _name = "bvpasa_cuota_sen.facturas_cuota_sen"
    _order = "id asc"

    partner_id = fields.Many2one('res.partner', string="Cliente", copy=False, required=True)
    factura_cuota_sen_id = fields.Many2one('account.move', string="Factura Cuota S.E.N.", copy=False, required=True)
    sen_saldo_inicial = fields.Float(string="Saldo Anterior", copy=False)
    sen_currency_id = fields.Many2one(string="Moneda Factura S.E.N.", related="factura_cuota_sen_id.currency_id",
                                      copy=False, required=True)
    factura_id = fields.Many2one('account.move', string="Factura", copy=False)
    factura_fecha = fields.Date(string="Fecha de Factura", related="factura_id.invoice_date")
    factura_currency_id = fields.Many2one(string="Moneda Factura", related="factura_id.currency_id", copy=False)
    nota_credito_id = fields.Many2one('account.move', string="Nota de Credito", copy=False)
    nc_fecha = fields.Date(string="Fecha de Nota de Crédito", related="nota_credito_id.invoice_date")
    nc_monto = fields.Float(string="Monto NC", copy=False)
    nc_fecha = fields.Date(string="Fecha de Nota de Credito", related="nota_credito_id.invoice_date")
    nc_currency_id = fields.Many2one(string="Moneda Nota de Credito", related="nota_credito_id.currency_id", copy=False)
    nc_tipo_cambio = fields.Float(string="Tipo de Cambio", copy=False)
    sen_saldo_final = fields.Float(string="Saldo Final", copy=False, required=False, compute="saldoFinal")
    active = fields.Boolean(string="Activo", default=True, copy=False)

    def saldoFinal(self):
        for sen in self:
            if type(sen.id) == int:
                linea_previa = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search(
                    [('factura_cuota_sen_id', '=', sen.factura_cuota_sen_id.id),
                     ('id', '<', sen.id),
                     ('nota_credito_id', '!=', False),
                     ('active', '=', True)],
                    limit=1, order="id desc")

                product_ingresos_anticipados_id = self.env['ir.config_parameter'].sudo().get_param(
                    'product_ingresos_anticipados_id')
                if not sen.factura_id and not sen.nota_credito_id:
                    saldo_cuota_sen = sum(sen.mapped('factura_cuota_sen_id.invoice_line_ids').filtered(
                        lambda x: x.product_id.id == int(product_ingresos_anticipados_id)).mapped('price_total'))
                    sen.sen_saldo_inicial = saldo_cuota_sen
                    sen.sen_saldo_final = sen.sen_saldo_inicial - sen.nc_monto
                elif linea_previa:
                    sen.sen_saldo_inicial = linea_previa.sen_saldo_final
                    sen.sen_saldo_final = sen.sen_saldo_inicial - sen.nc_monto
                else:
                    saldo_cuota_sen = sum(sen.mapped('factura_cuota_sen_id.invoice_line_ids').filtered(
                        lambda x: x.product_id.id == int(product_ingresos_anticipados_id)).mapped('price_total'))
                    sen.sen_saldo_inicial = saldo_cuota_sen
                    sen.sen_saldo_final = sen.sen_saldo_inicial - sen.nc_monto
            else:
                sen.sen_saldo_final = 0

    @api.model
    def setearFacturaSen(self):
        registros = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search([('active', '=', True)])
        for r in registros:
            r.write({'active':False})
            r.partner_id.write({'factura_cuota_sen_id':False})


class AccountMove(models.Model):
    _inherit = 'account.move'

    factura_cuota_sen = fields.Boolean(string="Factura Cuota SEN", default=False, copy=False)
    mensaje_nc_cuota_sen = fields.Char(string="Mensaje cuota SEN", default=False, copy=False,
                                       compute="computeMensajeNcCuotaSen")

    def button_anular(self):
        res = super(AccountMove, self).button_anular()
        for sen in self:
            if sen.move_type == 'out_refund':
                nc_sen = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search([('nota_credito_id', '=', sen.id),('active','=',True)])
                if nc_sen:
                    nc_sen.unlink()
            elif sen.move_type == 'out_invoice':
                factura_sen = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search([('factura_id', '=', sen.id),('active','=',True)])
                for f in factura_sen:
                    f.unlink()
                factura_sen = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search([('factura_cuota_sen_id', '=', sen.id),('active','=',True)])
                if factura_sen:
                    factura_sen.partner_id.write({'factura_cuota_sen_id':False})
                    for f in factura_sen:
                        f.unlink()
        return res

    def _post(self, soft=True):
        for sen in self:
            if sen.move_type == 'out_refund' and sen.partner_id.factura_cuota_sen_id:
                last_line_cuota_sen = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search(
                    [('factura_cuota_sen_id', '=', sen.partner_id.factura_cuota_sen_id.id),('active','=',True)],
                    limit=1, order='id desc')
                if last_line_cuota_sen and last_line_cuota_sen.sen_saldo_final > 0:
                    currency_rate = 1
                    if sen.currency_id != last_line_cuota_sen.sen_currency_id:
                        _get_conversion_rate = last_line_cuota_sen.sen_currency_id._get_conversion_rate_tipo_cambio_comprador
                        currency_rate = _get_conversion_rate(
                            last_line_cuota_sen.sen_currency_id,
                            self.company_id.currency_id,
                            self.company_id,
                            (self.date or self.invoice_date or fields.date.today())
                        )
                        monto_usd = sen.amount_total / currency_rate
                    else:
                        monto_usd = sen.amount_total
                    if monto_usd > last_line_cuota_sen.sen_saldo_final:
                        monto_usd = last_line_cuota_sen.sen_saldo_final
                    linea_sen_anterior = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search([('factura_id','=',sen.reversed_entry_id.id),
                                                                                                 ('nota_credito_id','=',sen.id),
                                                                                                 ('factura_cuota_sen_id','=',sen.partner_id.factura_cuota_sen_id.id)])
                    if linea_sen_anterior:
                        linea_sen_anterior.write({
                            'partner_id': sen.partner_id.id,
                            'sen_saldo_inicial': last_line_cuota_sen.sen_saldo_final,
                            'nc_monto': monto_usd,
                            'nc_tipo_cambio': currency_rate,
                            'sen_saldo_final': last_line_cuota_sen.sen_saldo_final - monto_usd
                        })
                    else:
                        vals = {
                            'partner_id': sen.partner_id.id,
                            'factura_cuota_sen_id': sen.partner_id.factura_cuota_sen_id.id,
                            'sen_saldo_inicial': last_line_cuota_sen.sen_saldo_final,
                            'nc_monto': monto_usd,
                            'nota_credito_id': sen.id,
                            'nc_tipo_cambio': currency_rate,
                            'sen_saldo_final': last_line_cuota_sen.sen_saldo_final - monto_usd,
                            'factura_id': sen.reversed_entry_id.id
                        }
                        self.env['bvpasa_cuota_sen.facturas_cuota_sen'].create(vals)
        res = super(AccountMove, self)._post(soft=soft)
        return res

    def action_post(self):
        for sen in self:
            if sen.factura_cuota_sen:
                product_servicio_sen_id = self.env['ir.config_parameter'].sudo().get_param(
                    'product_servicio_sen_id')
                product_ingresos_anticipados_id = self.env['ir.config_parameter'].sudo().get_param(
                    'product_ingresos_anticipados_id')
                if not product_servicio_sen_id or not product_ingresos_anticipados_id:
                    raise exceptions.UserError("Debe definir los productos de Cuota S.E.N.")

                if not int(product_ingresos_anticipados_id) in sen.mapped('invoice_line_ids.product_id.id') or \
                        not int(product_servicio_sen_id) in sen.mapped('invoice_line_ids.product_id.id'):
                    raise exceptions.UserError(
                        "Los productos de Cuota S.E.N. no se encuentran en las líneas de factura")

                saldo_cuota_sen = sum(sen.mapped('invoice_line_ids').filtered(
                    lambda x: x.product_id.id == int(product_ingresos_anticipados_id)).mapped('price_total'))

                sen.partner_id.write({'factura_cuota_sen_id': sen.id})
                vals = {
                    'partner_id': sen.partner_id.id,
                    'factura_cuota_sen_id': sen.id,
                    'sen_saldo_inicial': saldo_cuota_sen,
                    'sen_saldo_final': saldo_cuota_sen,
                    'active': True
                }
                self.env['bvpasa_cuota_sen.facturas_cuota_sen'].create(vals)
        res = super(AccountMove, self).action_post()
        return res

    @api.depends('partner_id', 'state', 'amount_residual', 'move_type')
    @api.onchange('partner_id', 'state', 'amount_residual', 'move_type')
    def computeMensajeNcCuotaSen(self):
        for sen in self:
            sen.write({'mensaje_nc_cuota_sen': False})
            if sen.partner_id.factura_cuota_sen_id and sen.state == 'posted' and sen.amount_residual > 0 \
                    and sen.move_type == 'out_invoice' and not sen.factura_cuota_sen:
                last_line_cuota_sen = self.env['bvpasa_cuota_sen.facturas_cuota_sen'].search(
                    [('factura_cuota_sen_id', '=', sen.partner_id.factura_cuota_sen_id.id),('active','=',True)],
                    limit=1, order='id desc')
                if last_line_cuota_sen and last_line_cuota_sen.sen_saldo_final > 0:
                    _get_conversion_rate = last_line_cuota_sen.sen_currency_id._get_conversion_rate_tipo_cambio_comprador
                    currency_rate = _get_conversion_rate(
                        last_line_cuota_sen.sen_currency_id,
                        self.company_id.currency_id,
                        self.company_id,
                        (self.date or self.invoice_date or fields.date.today())
                    )
                    monto_gs = last_line_cuota_sen.sen_saldo_final * currency_rate
                    mensaje = "El cliente cuenta con un saldo a favor de USD " + str(
                        '{0:,.0f}'.format(last_line_cuota_sen.sen_saldo_final)).replace(",", ".") + " (" + \
                              str('{0:,.0f}'.format(int(monto_gs))).replace(",", ".") + "Gs.). Debe generar una Nota " \
                                                                                        "de Crédito."

                    sen.write({'mensaje_nc_cuota_sen': mensaje})