from locale import currency
from odoo import models, api, fields, exceptions,_
from odoo.exceptions import UserError,ValidationError
import qrcode
import base64,hashlib
from io import BytesIO
from . import amount_to_text_spanish


class AccountMove(models.Model):
    _inherit = 'account.move'

    qr_code = fields.Binary(string="QR Code", compute="generate_qr_code")
    nro_nota_remision = fields.Char(string="Nro. Nota de remisión")


    def genera_token(self,id_factura):
        palabra=id_factura+"amakakeruriunohirameki"
        return hashlib.sha256(bytes(palabra,'utf-8')).hexdigest()

    
    def amount_to_text(self, amount,a=False):
        convert_amount_in_words = self.env['interfaces_tools.tools'].numero_a_letra(amount)
        return convert_amount_in_words

    def format_monto(self,monto):
        return self.env['interfaces_tools.tools'].format_amount(monto,currency=self.currency_id)


    def generate_qr_code(self):
        for i in self:
            base_url = self.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            route = "/invoice_check?invoice_id="+str(i.id)+"&token="+i.genera_token(str(i.id))
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data("%s%s" % (base_url, route))
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            i.qr_code = qr_image


    def format_linea_autoimpresor(self, linea=False):
        limite = 50
        if not linea:
            return False
        else:
            linea_limitada = []
            linea_actual = ''
            c = 0
            for i in linea:
                c += 1
                linea_actual += i
                if c == limite:
                    linea_limitada.append(linea_actual)
                    linea_actual = ''
                    c = 0
            if linea_actual: linea_limitada.append(linea_actual)
            return linea_limitada

    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Sólo las facturas se pueden imprimir"))

        self.filtered(lambda inv: not inv.invoice_sent).write({'invoice_sent': True})
        
        return self.env.ref('factura_autoimpresor.factura_report_action').report_action(self)

