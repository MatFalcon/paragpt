from odoo import fields, api, models, exceptions
import re

class Timbrado(models.Model):
    _name = 'interfaces_timbrado.timbrado'

    name = fields.Char('Nro. de timbrado', required=True)
    tipo_documento = fields.Selection(string="Tipo de documento", selection=[('out_invoice', 'Factura'), (
        'out_refund', 'Nota de credito'), ('nota_remision', 'Nota de remision')], default="out_invoice")
    inicio_vigencia = fields.Date(
        string='Fecha de inicio de vigencia', default=fields.Date.today(), required=True)
    fin_vigencia = fields.Date(
        string='Fecha de fin de vigencia', required=True)
    nro_establecimiento = fields.Char('Nro. de establecimiento', required=True)
    nro_punto_expedicion = fields.Char(
        'Nro. punto de expedición', required=True)
    rango_inicial = fields.Integer('Número de factura inicial', required=True)
    rango_final = fields.Integer('Número de factura final', required=True)
    proximo_numero = fields.Integer('Próximo número', required=True)
    active = fields.Boolean(string='Activo', default=True)
    journal_id = fields.Many2one(
        'account.journal', string='Diario de venta')
    company_id = fields.Many2one(
        'res.company', string='Compañía', default=lambda self: self.env.user.company_id.id)

    @api.model
    def create(self, vals):
        rec = super(Timbrado, self).create(vals)
        #rec.actualiza_sequencia(vals)
        rec.validar_formato_timbrado(vals['name'])
        return rec

    def write(self, vals):
        res=super(Timbrado, self).write(vals)
        #if 'nro_establecimiento' in vals or 'nro_punto_expedicion' in vals or 'proximo_numero' in vals:
        #    self.actualiza_sequencia(vals)
        if 'name' in vals:
            self.validar_formato_timbrado(vals['name'])
        return res

    @api.model
    def actualiza_sequencia(self, vals):
        if self.journal_id:
            var_nro_establecimiento = self.nro_establecimiento
            var_nro_punto_expedicion = self.nro_punto_expedicion
            var_proximo_numero = self.proximo_numero
            if vals:
                if 'nro_establecimiento' in vals:
                    var_nro_establecimiento = vals['nro_establecimiento']

                if 'nro_punto_expedicion' in vals:
                    var_nro_punto_expedicion = vals['nro_punto_expedicion']

                if 'proximo_numero' in vals:
                    var_proximo_numero = vals['proximo_numero']
            if self.tipo_documento=='out_invoice':
                seq = self.journal_id.sequence
            elif self.tipo_documento=='out_refund':
                seq = self.journal_id.refund_sequence_id
                s = {
                    'use_date_range': False,
                    'prefix': var_nro_establecimiento + '-' + var_nro_punto_expedicion + '-',
                    'number_increment': 1,
                    'padding': 7,
                    'number_next_actual': var_proximo_numero

                }
                seq.write(s)
                if self.tipo_documento=='out_refund':
                    self.journal_id.write({'refund_sequence':True})
        elif 'journal_id' in vals:
            journal = self.env['account.journal'].browse(vals['journal_id'])
            var_nro_establecimiento = vals['nro_establecimiento']
            var_nro_punto_expedicion = vals['nro_punto_expedicion']
            var_proximo_numero = vals['proximo_numero']
            if self.tipo_documento=='out_invoice':
                seq = journal.sequence
            elif self.tipo_documento=='out_refund':
                seq = journal.refund_sequence_id
            s = {
                'use_date_range': False,
                'prefix': var_nro_establecimiento + '-' + var_nro_punto_expedicion + '-',
                'number_increment': 1,
                'padding': 7,
                'number_next_actual': var_proximo_numero
            }
            seq.write(s)
            if self.tipo_documento=='out_refund':
                journal.write({'refund_sequence':True})
        else:
            raise exceptions.ValidationError('Debe tener un Diario asignado')

    def desactivar_otros_timbrados(self, vals):
        journal = self.journal_id or self.env['account.journal'].browse(
            vals['journal_id'])
        otros_timbrados = journal.timbrados_ids.filtered(
            lambda x: x.id != self.id or vals['id'])
        for i in otros_timbrados:
            i.write({'active': False})

    def validar_formato_timbrado(self, seq):
        patron = re.compile(r'(^\d{8}$){1}')
        # if not self.es_autofactura:
        if seq:
            m = patron.match(seq)
            if m is None:
                raise exceptions.ValidationError('El nro de timbrado no tiene el formato adecuado (8 digitos)')
