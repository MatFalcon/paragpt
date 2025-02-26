from odoo import models,api,fields,exceptions


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    pie_factura=fields.Html(string="Pie de factura")
    mostrar_qr=fields.Boolean(string="Mostrar QR en autoimpresor")
