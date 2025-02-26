# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.account.controllers.portal import PortalAccount
import hashlib


class FacturaAutoimpresorPortalAccount(PortalAccount):
    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        # factura_autoimpresor/controllers/portal.py
        try:
            invoice_sudo = self._document_check_access('account.move', invoice_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')

        if report_type in ('html', 'pdf', 'text'):
            report_ref = 'account.account_invoices'
            mail_template = request.env.ref(invoice_sudo._get_mail_template(), raise_if_not_found=False)
            if mail_template and mail_template.sudo().report_template:
                report_ref = mail_template.report_template.get_external_id().get(mail_template.report_template.id)

            return self._show_report(model=invoice_sudo, report_type=report_type, report_ref=report_ref, download=download)

        values = self._invoice_get_page_view_values(invoice_sudo, access_token, **kw)
        return request.render("account.portal_invoice_page", values)
