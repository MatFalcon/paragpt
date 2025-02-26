from odoo import models, fields, api, exceptions, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    tipo_pago = fields.Selection(string='Tipo de pago', selection=[('Efectivo', 'Efectivo'), ('Cheque', 'Cheque'),
                                                                   ('TCredito',
                                                                    'Tarjeta de crédito'),
                                                                   ('TDebito',
                                                                    'Tarjeta de débito'),
                                                                   ('Transferencia',
                                                                    'Transferencia / Depósito'),
                                                                   ('Retencion', 'Retención'), ('Otros', 'Otros')])
    nro_cheque = fields.Char(string='Nro. de cheque')
    bank_id = fields.Many2one('res.bank', string='Banco')
    fecha_cheque = fields.Date(string="Fecha del cheque")
    fecha_vencimiento_cheque = fields.Date(
        string="Fecha de vencimiento del cheque")
    nro_cuenta = fields.Char(string="Nro. de cuenta")
    nro_documento = fields.Char(string="Nro. de documento")
    observaciones = fields.Char(string="Observaciones")
    nro_recibo = fields.Char(string="Nro. de recibo", copy=False)


class ReporteRecibo(models.AbstractModel):
    _name = 'report.interfaces_payment.reporte_pagos_editado_multi'

    @api.model
    def _get_report_values(self, docids, data=None):
        recibo_name = 0
        partner = 0
        monto_total = 0
        fecha = 0
        facturas = 0
        moneda = 0
        payments = self.env['account.payment'].browse(docids)

        if payments:
            for i in payments:
                if not i.partner_id:
                    raise exceptions.UserError(
                        _('Los pagos deben tener un cliente'))
            if len(list(set(payments.mapped("state")))) > 1:
                raise exceptions.UserError(
                    _('Los pagos deben estar Publicados'))
            if list(set(payments.mapped("state")))[0] != "posted":
                raise exceptions.UserError(
                    _('Los pagos deben estar en estado Publicado'))
            if len(payments.mapped("partner_id")) > 1:
                raise exceptions.UserError(
                    _('Debe seleccionar pagos de solo un cliente'))
            if len(payments.mapped("currency_id")) > 1:
                raise exceptions.UserError(
                    _('Los pagos deben de ser de una sola moneda'))
            if len(list(set(payments.mapped("nro_recibo")))) > 1:
                raise exceptions.UserError(
                    _('Debe seleccionar el mismo Nro OP'))

            else:
                recibo_name = list(set(payments.mapped("nro_recibo")))
                partner = payments.mapped("partner_id")
                moneda = payments.mapped("currency_id")
                facturas = payments.mapped('reconciled_invoice_ids')
                fecha = payments[0].date
                for payment in payments:
                    monto_total += payment.amount
            return {

                'payments': payments,
                'facturas': facturas,
                'recibo_name': recibo_name[0],
                'fecha': fecha.strftime('%d/%m/%Y'),
                'partner': partner,
                'moneda': moneda,
                'monto_total': monto_total,
                'usuario': self.env.user,
            }


class ReporteOrdenPago(models.AbstractModel):
    _name = 'report.interfaces_payment.reporte_orden_pago'

    @api.model
    def _get_report_values(self, docids, data=None):
        recibo_name = []
        orden_name = 0
        partner = 0
        monto_total = 0
        fecha = 0
        facturas = 0
        moneda = 0
        payments = self.env['account.payment'].browse(docids)

        if payments:
            for i in payments:
                if not i.partner_id:
                    raise exceptions.UserError(
                        _('La orden debe tener un cliente'))
            if len(list(set(payments.mapped("state")))) > 1:
                raise exceptions.UserError(
                    _('Los pagos deben estar Publicados'))
            if list(set(payments.mapped("state")))[0] != "posted":
                raise exceptions.UserError(
                    _('Los pagos deben estar en estado Publicado'))
            if len(payments.mapped("partner_id")) > 1:
                raise exceptions.UserError(
                    _('Debe seleccionar solo un cliente'))
            if len(payments.mapped("currency_id")) > 1:
                raise exceptions.UserError(
                    _('Los pagos deben de ser de una sola moneda'))
            if len(list(set(payments.mapped("nro_recibo")))) != 1:
                raise exceptions.UserError(
                    _('Debe seleccionar el mismo Nro OP'))
            if len(list(set(payments.mapped("journal_id")))) != 1:
                raise exceptions.UserError(
                    _('Debe seleccionar el mismo Diario'))

            else:
                recibo_name = list(set(payments.mapped("name")))
                if not recibo_name or not any(recibo_name): recibo_name = []
                partner = payments.mapped("partner_id")
                moneda = payments.mapped("currency_id")
                # facturas = payments.mapped('reconciled_invoice_ids')
                fecha = payments[0].date
                monto_total = sum(payments.mapped('amount'))
                monto_total = sum(payments.mapped('move_id.line_ids.debit'))
                diario = payments.mapped("journal_id")

            return {
                'recibo_name': recibo_name,
                'payments': payments,
                # 'facturas': facturas,
                'fecha': fecha,
                'partner': partner,
                'moneda': moneda,
                'monto_total': monto_total,
                'usuario': self.env.user,
                'company': self.env.company,
                'diario': diario,
            }
