from odoo import models, fields,api

class PresaleRicohConfig(models.Model):
    _name = 'presale.ricoh.config'
    _description = 'Configuracion de Preventas Ricoh'

    name = fields.Char(string='Nombre', required=True, default='Configuracion Principal')
    ld = fields.Float(string='LD')
    gm = fields.Float(string='GM')
    intereses = fields.Float(string='Intereses')
    iva = fields.Float(string='IVA', default=1.1)


class PresaleRicohIntereses(models.Model):
    _name = 'presale.ricoh.intereses'
    _description = 'Intereses de Preventas Ricoh'
    
    name = fields.Char(compute="_compute_name")
    plazo = fields.Integer(string='Plazo')
    porcentaje = fields.Float(string='Porcentaje')

    @api.depends("plazo")
    def _compute_name(self):
        for record in self:
            record.name = str(record.plazo)