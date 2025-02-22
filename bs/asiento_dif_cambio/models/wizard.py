from email.policy import default
from odoo import api, fields, models
import datetime


class WizardMove(models.TransientModel):
    _name = 'asientos_dif_cambios.wizard_move'
    _description = 'wizard de asiento contable'
    fecha_fin = fields.Date(string='Fecha fin', default=False)
    currency_rate_compra = fields.Float(string='Cotización Compra', default=0.0)
    currency_rate_venta = fields.Float(string='Cotización Venta', default=0.0)

    def create_move(self):
        journal_id = self.env['account.journal'].search([('name', '=', 'Diferencia de cambio')])

        asiento = {
            'date': self.fecha_fin,
            'journal_id': journal_id.id,
            'ref': 'Asiento por diferencia de cambio (Cuentas Activas)',
            'currency_rate': self.currency_rate_compra,
        }
        move_id = self.env['account.move'].create(asiento)
        asiento = {
            'date': self.fecha_fin,
            'journal_id': journal_id.id,
            'ref': 'Asiento por diferencia de cambio (Cuentas Pasivas)',
            'currency_rate': self.currency_rate_venta,
        }
        move_id_2 = self.env['account.move'].create(asiento)

        move_id.create_asiento_mas(self.fecha_fin)
        move_id_2.create_asiento_menos(self.fecha_fin)

