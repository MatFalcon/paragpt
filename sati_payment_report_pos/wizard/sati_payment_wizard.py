# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ReportWizardPOSExtension(models.TransientModel):
    _inherit = 'sati_payment_report.wizard'

    # Si deseas, puedes agregar o reutilizar campos adicionales
    analytic_account_ids = fields.Many2many('account.analytic.account', string='Analytic accounts')
    detallado = fields.Boolean(string='Informe detallado?')
    tipo_informe = fields.Selection(
        selection=[('recibos', 'Fecha de recibo/op'), ('pago', 'Fecha de pago')],
        string="Filtro de fecha basado en"
    )

    def get_pos_payments(self):
        """Obtiene los pagos del módulo POS según el dominio definido."""
        domain = [
            ('payment_date', '>=', self.start_date),
            ('payment_date', '<=', self.end_date),
            ('payment_method_id.journal_id', 'in', self.journal_ids.ids),
        ]
        pos_payments = self.env['pos.payment'].search(domain, order='create_date')
        return pos_payments
