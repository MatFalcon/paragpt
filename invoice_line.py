from odoo import models, fields, api
from num2words import num2words
import random
from odoo.exceptions import ValidationError
import logging

_logger= logging.getLogger(__name__)


class Invoice_line_FactElect(models.Model):
    _inherit = 'account.move.line'

    #Campos para productos agricolas/agrocquimico
    # Expuestos en  E8.4. Grupo de rastreo de la mercadería (E750-E760) del MT150

    nro_lote_fe= fields.Char(string='Nro Lote FE',size=80)
    fecha_vencimiento_fe = fields.Date(string="Fecha de Vencimiento prod. FE")
    nro_serie_fe= fields.Char(string='Nro Lote FE',size=10)
    nro_pedido_fe= fields.Char(string='Nro Pedido FE',size=20)
    nro_seguimiento_fe= fields.Char(string='Nro Seguimiento FE',size=20)
    nombre_importador_fe= fields.Char(string='Nombre importador FE',size=60)
    direccion_importador_fe= fields.Char(string='Direccion importador FE',size=255)
    nro_registro_imp_fe= fields.Char(string='Nro Registro Importador FE',size=20)
    nro_registro_senave_producto= fields.Char(string='Nro Registro del Producto del SENAVE',size=20)
    nro_registro_senave_entidad_comercial= fields.Char(string='Nro Registro de la entidad comercial otorgado por el SENAVE',size=20)
    porcentaje_descuento = fields.Float(string="%  particular")
    monto_anticipo = fields.Float(string="Monto particular")
    tiene_descuento = fields.Boolean(string="Es descuento", default=False)
    tiene_anticipo = fields.Boolean(string="Es Anticipo", default=False)

    lot_ids = fields.Many2many(
        'stock.lot',
        string="Números de Serie",
        compute="_compute_lot_ids",
        readonly=False
    )

    @api.depends('move_id', 'product_id')
    def _compute_lot_ids(self):
        for line in self:
            if line.lot_ids:
                continue

            lot_numbers = self.env['stock.lot']

            if not line.product_id or not line.move_id or not line.move_id.invoice_origin:
                line.lot_ids = False
                continue

            stock_pickings = self.env['stock.picking'].search([
                ('origin', '=', line.move_id.invoice_origin)
            ])
            if not stock_pickings:
                print(f"[DEBUG] No se encontraron pickings para: {line.move_id.invoice_origin}")

            for picking in stock_pickings:
                stock_moves = self.env['stock.move'].search([
                    ('picking_id', '=', picking.id),
                    ('product_id', '=', line.product_id.id)
                ])
                lot_numbers |= stock_moves.mapped('move_line_ids.lot_id')

            if not line.lot_ids:
                line.lot_ids = lot_numbers

class AccountMoveSend(models.TransientModel):
    _inherit = 'account.move.send'

    @api.model
    def _prepare_invoice_pdf_report(self, invoice, invoice_data):
        """ Prepare the pdf report for the invoice passed as parameter.
        :param invoice:         An account.move record.
        :param invoice_data:    The collected data for the invoice so far.
        """

        if invoice.invoice_pdf_report_id:
            return
        # _logger.info('teeeron')
        content, _report_format = self.env['ir.actions.report']._render('factura_electronica.factura_report_2',
                                                                        invoice.ids)

        invoice_data['pdf_attachment_values'] = {
            'raw': content,
            'name': invoice._get_invoice_report_filename(),
            'mimetype': 'application/pdf',
            'res_model': invoice._name,
            'res_id': invoice.id,
            'res_field': 'invoice_pdf_report_file',  # Binary field
        }
