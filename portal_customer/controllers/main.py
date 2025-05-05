from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request, route
from odoo import http, _
from odoo.exceptions import AccessError, MissingError

class CustomInvoicePortal(CustomerPortal):

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        print("portal_my_invoice_detail mio")

        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            return self._show_report(
                model=invoice_sudo,
                report_type=report_type,
                report_ref='portal_customer.factura_report_web',
                download=download
            )

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        return request.render("account.portal_invoice_page", values)
