from odoo import models, fields, api

class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = 'sale.advance.payment.inv'

    class SaleAdvancePaymentInvInherit(models.TransientModel):
        _inherit = 'sale.advance.payment.inv'


        def create_invoices(self):
            # Llama al método original
            res = super().create_invoices()
            # Accede a las facturas creadas desde el contexto
            created_invoice_ids = self.env['sale.order'].env.context.get('created_invoices', [])
            if created_invoice_ids:
                invoice_id = created_invoice_ids[0]  # Asumiendo que solo se crea una factura

                invoice_term_id = self._context.get('invoice_term_id')
                if invoice_term_id:
                    invoice_term = self.env['sale.invoice.terms'].browse(invoice_term_id)
                    invoice_term.write({
                        'state': 'invoiced',
                        'invoice_id': invoice_id,
                    })
                    if invoice_term.sale_order_id.generate_account_move:
                        invoice_term.generate_cancel_provition_move()

            return res


