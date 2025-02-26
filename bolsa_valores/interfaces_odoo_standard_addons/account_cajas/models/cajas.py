from odoo import fields, api, models, exceptions


class AccountCaja(models.Model):
    _name = 'account.caja'

    name = fields.Char(string="Nombre", required=True)
    journal_ids = fields.Many2many('account.journal', string="Diarios de pago", domain=[
                                   ('type', 'in', ['bank', 'cash']),('diario_caja','=',True)], required=True)
    sequence_id = fields.Many2one('ir.sequence', string="Secuencia")
    active = fields.Boolean(string="Activo", default=True)

    
    def crea_sequence(self,name):
        seq = {'name': 'Secuencia de sesion de caja '+name,
               'implementation': 'no_gap',
               'padding': 4,
               'number_increment': 1,
               'number_next_actual': 1,
               'use_date_range': True,
               'prefix': name+"/"+'%(year)s/%(month)s/%(day)s/',
               }
        sequence = self.env['ir.sequence'].sudo().create(seq)
        return sequence

    @api.model
    def create(self, vals):
        vals['sequence_id'] = self.crea_sequence(vals.get('name')).id
        return super(AccountCaja, self).create(vals)
