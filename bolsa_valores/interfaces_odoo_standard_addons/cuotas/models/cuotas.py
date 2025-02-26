
from locale import currency
from odoo import api, fields, models, exceptions
import datetime
import uuid
import json


class Cuotas(models.Model):
    _name = 'cuotas.cuota'
    _inherit = ['portal.mixin', 'mail.thread',
                'mail.activity.mixin', 'utm.mixin']
    _description = 'Cuota'
    _order = 'id desc'

    name = fields.Char(string="Número de cuota", readonly=True,
                       required=True, default="Borrador", tracking=True)
    tipo_cuota = fields.Selection(string="Tipo de cuota", selection=[(
        'sale', 'Ingreso'), ('purchase', 'Egreso')], required=True, default='sale', tracking=True)
    partner_id = fields.Many2one(
        'res.partner', string="Empresa", required=True, tracking=True)
    phone = fields.Char(related="partner_id.phone",
                        string="Teléfono", tracking=True)
    currency_id = fields.Many2one('res.currency', string="Moneda",
                                  default=lambda self: self.env.company.currency_id, required=True, tracking=True)
    monto_cuota = fields.Monetary(string="Monto cuota", tracking=True)
    descuento_porcentaje = fields.Float(string="Descuento %", tracking=True)
    descuento_monto = fields.Float(string="Descuento monto", tracking=True)
    fecha_vencimiento = fields.Date(
        string="Fecha de vencimiento", required=True, tracking=True)
    product_id = fields.Many2one(
        'product.product', string="Producto", required=True, tracking=True)
    fecha_facturacion = fields.Date(
        string="Fecha de facturacion", tracking=True)
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string="Cuenta Analítica")
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string="Etiquetas analíticas")
    state = fields.Selection(string="Estado", selection=[('draft', 'Borrador'), (
        'confirmado', 'Confirmado'), ('cancel', 'Cancelado')], default="draft")
    payment_state = fields.Selection(string="Estado de pago", selection=[('not_paid', 'Pendiente'), (
        'paid', 'Pagado')], compute="compute_estado_pago", default="not_paid", tracking=True, store=True)
    invoice_id = fields.Many2one(
        'account.move', string="Factura", copy=False, readonly=True, tracking=True)
    invoice_ids = fields.Many2many('account.move', string="Facturas")
    invoice_count = fields.Integer(
        string="Cantidad de facturas", compute="compute_invoices")

    vencida = fields.Boolean(string="Vencida", compute="compute_vencida")
    monto_facturado = fields.Monetary(
        string="Monto facturado", compute="compute_totalmente_facturado", store="True")
    monto_a_facturar = fields.Monetary(
        string="Monto a facturar", compute="compute_totalmente_facturado", store="True")
    monto_neto_cuota = fields.Monetary(
        string="Monto neto cuota", compute="compute_totalmente_facturado", store="True")

    totalmente_facturado = fields.Boolean(
        string="Totalmente facturado", compute="compute_totalmente_facturado", store="True")
    totalmente_facturado_aux = fields.Boolean(
        string="Totalmente facturado auxiliar", compute="compute_totalmente_facturado")
    nro_cuota = fields.Char(string="Cuota", copy=False)
    fecha_pago = fields.Date(string="Fecha de pago",
                             compute="compute_estado_pago", store=True)
    company_id=fields.Many2one('res.company',string="Compañía",default=lambda self:self.env.company)
    amount_signed=fields.Monetary(string="Monto con signo",compute="compute_amount_signed",store=True)

    @api.onchange('monto_cuota')
    @api.depends('monto_cuota','tipo_cuota')
    def compute_amount_signed(self):
        for i in self:
            if i.tipo_cuota=='purchase':
                monto=i.monto_cuota * -1
            else:
                monto=i.monto_cuota
            if i.currency_id!=self.env.company.currency_id:
                monto=i.currency_id._convert(monto,self.env.company.currency_id,self.env.company,datetime.date.today())
            i.amount_signed=monto
    
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
                raise exceptions.ValidationError(
                    'No se puede confirmar cuotas que no estén en borrador')
        self.write({'state': 'confirmado'})

    @api.depends('invoice_ids', 'invoice_ids.payment_state', 'totalmente_facturado', 'monto_cuota')
    @api.onchange('invoice_ids', 'invoice_ids.payment_state', 'totalmente_facturado', 'monto_cuota')
    def compute_estado_pago(self):
        for i in self:
            if i.totalmente_facturado:
                total_residual = sum(i.invoice_ids.filtered(
                    lambda x: x.state == 'posted' and x.payment_state != 'reversed').mapped('amount_residual'))
                if total_residual != 0:
                    i.payment_state = 'not_paid'
                else:
                    i.payment_state = 'paid'
            else:
                i.payment_state = "not_paid"

    @api.depends('invoice_ids', 'invoice_ids.state', 'monto_cuota', 'descuento_porcentaje')
    @api.onchange('invoice_ids', 'invoice_ids.state', 'monto_cuota', 'descuento_porcentaje')
    def compute_totalmente_facturado(self):
        for i in self:
            invoices_total = sum(i.invoice_ids.filtered(
                lambda x: x.state == 'posted' and x.payment_state != 'reversed').mapped('invoice_line_ids').filtered(
                lambda z: z.cuota_id == i).mapped(
                'price_total'))
            i.monto_facturado = invoices_total

            i.monto_neto_cuota = i.monto_cuota - \
                (i.monto_cuota * i.descuento_porcentaje / 100)
            i.monto_a_facturar = i.monto_neto_cuota - i.monto_facturado
            if i.monto_a_facturar < 0:
                i.monto_a_facturar = 0
            if invoices_total >= i.monto_neto_cuota:
                i.totalmente_facturado = True
                i.totalmente_facturado_aux = True
            else:
                i.totalmente_facturado = False
                i.totalmente_facturado_aux = False

    def compute_invoices(self):
        for i in self:
            i.invoice_count = len(self.invoice_ids)
            if i.invoice_count > 1:
                for inv in self.invoice_ids:
                    if inv.payment_state in ['in_payment', 'paid']:
                        if inv.invoice_payments_widget and 'content' in inv.invoice_payments_widget:
                            fecha = json.loads(inv.invoice_payments_widget)[
                                'content'][0]['date'] or False
                            i.write({
                                'fecha_pago': fecha
                            })
                            break
            elif i.invoice_count == 1:
                if i.invoice_ids.payment_state in ['in_payment', 'paid']:
                    if i.invoice_ids.invoice_payments_widget and 'content' in i.invoice_ids.invoice_payments_widget:
                        fecha = json.loads(i.invoice_ids.invoice_payments_widget)[
                            'content'][0]['date'] or False
                        i.write({
                            'fecha_pago': fecha
                        })

    def compute_vencida(self):
        for i in self:
            hoy = datetime.date.today()
            if i.fecha_vencimiento < hoy and (i.payment_state == 'not_paid' or not i.payment_state):
                i.vencida = True
            else:
                i.vencida = False

    def button_generar_cuotas(self):
        view_id = self.env.ref('cuotas.wizard_generar_cuotas_form')
        return {
            'name': 'Generar cuotas',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'cuotas.wizard.generar.cuota',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    def action_cancelar(self):
        for i in self:
            if i.payment_state and i.payment_state != 'not_paid':
                raise exceptions.ValidationError(
                    'Sólo se pueden cancelar cuotas pendientes')
            else:
                if i.invoice_id and i.invoice_id.state not in ['cancel', 'draft']:
                    raise exceptions.ValidationError(
                        'La cuota cuenta con facturas publicadas')
            i.write({'state': 'cancel'})

    def action_marcar_pagado(self):
        for i in self:
            if i.state not in ['pendiente', 'parcial']:
                raise exceptions.ValidationError(
                    'Sólo se pueden marcar como pagadas las cuotas en estado Pendiente o Parcial')
        self.write({'state': 'pagado'})

    def unlink(self, force=False):
        if any(self.filtered(lambda x:x.state!='draft')) :
            raise exceptions.ValidationError(
                'Solo se pueden borrar cuotas en borrador')
        else:
            if any(self.filtered(lambda x:x.payment_state!='not_paid')):
                raise exceptions.ValidationError(
                    'Sólo se pueden eliminar cuotas pendientes')
        super(Cuotas, self).unlink()

    def obtener_numero(self):
        numero = self.env['ir.sequence'].sudo().next_by_code('seq_num_cuota')
        if not numero:
            raise exceptions.ValidationError(
                'No se encuentra la secuencia de números de cuota')
        return numero

    @api.model
    def create(self, vals):
        name = self.obtener_numero()
        vals['name'] = name
        return super(Cuotas, self).create(vals)

   
    @api.onchange('descuento_porcentaje')
    def validar_porcentaje(self):
        if self.descuento_porcentaje < 0 or self.descuento_porcentaje > 100:
            raise exceptions.ValidationError(
                'Porcentaje de descuento incorrecto')
        return

    def button_facturar(self):
        tipo=list(set(self.mapped('tipo_cuota')))
        if len(tipo)>1:
            raise exceptions.ValidationError('Debe elegir un sólo tipo de cuotas')
        
        view_id = self.env.ref('cuotas.wizard_facturar_form')
        return {
            'name': 'Generar factura',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'cuotas.wizard.facturar',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_cuotas_ids': [(6, 0, self.ids)],'default_tipo_cuota':tipo[0]}
        }

    def action_facturar(self, journal_id, estado_factura, fecha_factura=datetime.date.today(),
                        fecha_vencimiento=datetime.date.today()):
        cuotas = self
        partners = list(set(cuotas.mapped('partner_id')))
        tipo_cuota = list(set(cuotas.mapped('tipo_cuota')))
        if len(tipo_cuota) > 1:
            raise exceptions.ValidationError(
                "Debe elegir un sólo tipo de cuota")
        if tipo_cuota[0] == 'sale':
            move_type = 'out_invoice'
        else:
            move_type = 'in_invoice'
        if not partners:
            raise exceptions.ValidationError('Existen cuotas sin cliente')
        invoices = []
        for p in partners:
            cs = cuotas.filtered(lambda x: x.partner_id == p)
            lines = []
            currency = list(set(cs.mapped('currency_id')))
            if len(currency) > 1:
                raise exceptions.ValidationError(
                    'Existen cuotas con monedas diferentes. Favor verificar')
            else:
                currency = currency[0]

            for cuota in cs:

                account_id = False
                if cuota.tipo_cuota=='sale':
                    if cuota.product_id.property_account_income_id:
                        account_id = cuota.product_id.property_account_income_id.id
                    elif cuota.product_id.categ_id.property_account_income_categ_id:
                        account_id = cuota.product_id.categ_id.property_account_income_categ_id.id
                    elif journal_id.default_account_id:
                        account_id = journal_id.default_account_id.id
                elif cuota.tipo_cuota=='purchase':
                    if cuota.product_id.property_account_expense_id:
                        account_id = cuota.product_id.property_account_expense_id.id
                    elif cuota.product_id.categ_id.property_account_expense_categ_id:
                        account_id = cuota.product_id.categ_id.property_account_expense_categ_id.id
                    elif journal_id.default_account_id:
                        account_id = journal_id.default_account_id.id

                analytic_account_id = False
                analytic_tag_ids = False
                if cuota.analytic_account_id:
                    analytic_account_id = cuota.analytic_account_id.id
                if cuota.analytic_tag_ids:
                    analytic_tag_ids = [
                        (6, 0, cuota.analytic_tag_ids.ids)]

                if not account_id:
                    raise exceptions.ValidationError(
                        'No está definida la cuenta de contable del Producto, Categoría de producto o del Diario. Favor verificar')
                l = (0, 0, {
                    'product_id': cuota.product_id.id,
                    'name': cuota.product_id.display_name + ' - Cuota: ' + (cuota.nro_cuota or cuota.name),
                    'quantity': 1,
                    'price_unit': cuota.monto_a_facturar / (1 - (cuota.descuento_porcentaje / 100)),
                    'discount': cuota.descuento_porcentaje,
                    'tax_ids': [(6, 0, cuota.product_id.taxes_id.ids)],
                    'account_id': account_id,
                    'analytic_account_id': analytic_account_id or False,
                    'analytic_tag_ids': analytic_tag_ids or False,
                    'cuota_id': cuota.id,
                })
                lines.append(l)

            invoice = {
                'journal_id': journal_id.id,
                'partner_id': p.id,
                'invoice_date': fecha_factura or datetime.date.today(),
                'invoice_date_due': fecha_vencimiento or datetime.date.today(),
                'currency_id': currency.id,
                'move_type': move_type,
                'invoice_line_ids': lines
            }
            invoice_id = self.env['account.move'].create(invoice)
            if invoice_id:
                cs.write({'invoice_ids': [(4, invoice_id.id, 0)]})
                if estado_factura == 'posted':
                    invoice_id.action_post()
                invoices.append(invoice_id.id)
        return invoices

    @api.onchange('product_id')
    @api.depends('product_id')
    def onchange_product_id(self):
        for r in self:
            if r.product_id and r.product_id.list_price:
                r.monto_cuota = r.product_id.list_price

    def action_view_invoice(self):
        return {
            'name': 'Facturas generadas',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.invoice_ids.ids)]
        }
