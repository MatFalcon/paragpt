from odoo import models,fields,api,exceptions


class Timbrado(models.Model):
    _inherit = 'interfaces_timbrado.timbrado'


    @api.model
    def create(self, vals):
        rec = super(Timbrado, self).create(vals)
        rec.actualiza_sequencia(vals)
        return rec

    
    def write(self, vals):
        res=super(Timbrado, self).write(vals)
        if 'nro_establecimiento' in vals or 'nro_punto_expedicion' in vals or 'proximo_numero' in vals:
            self.actualiza_sequencia(vals)
        return res
   
    @api.model
    def actualiza_sequencia(self, vals):
        if self.journal_id:
            var_nro_establecimiento = self.nro_establecimiento
            var_nro_punto_expedicion = self.nro_punto_expedicion
            var_proximo_numero = self.proximo_numero
            seq=None
            if vals:
                if 'nro_establecimiento' in vals:
                    var_nro_establecimiento = vals['nro_establecimiento']

                if 'nro_punto_expedicion' in vals:
                    var_nro_punto_expedicion = vals['nro_punto_expedicion']

                if 'proximo_numero' in vals:
                    var_proximo_numero = vals['proximo_numero']
            if self.tipo_documento=='nota_remision':
                seq = self.journal_id.remision_sequence_id
           
            s = {
                'use_date_range': False,
                'prefix': var_nro_establecimiento + '-' + var_nro_punto_expedicion + '-',
                'number_increment': 1,
                'padding': 7,
                'number_next_actual': var_proximo_numero,

            }
            if not seq and self.tipo_documento=='nota_remision':
                seq=self.env['ir.sequence'].create({'name':self.journal_id.name + " Sequence Nota de remision",'implementation':'no_gap','padding':7,'number_increment':1,'company_id':self.env.company.id })
                self.journal_id.write({'remision_sequence_id':seq})
                seq=self.journal_id.remision_sequence_id
                seq.write(s)
        elif 'journal_id' in vals:
            journal = self.env['account.journal'].browse(vals['journal_id'])
            var_nro_establecimiento = vals['nro_establecimiento']
            var_nro_punto_expedicion = vals['nro_punto_expedicion']
            var_proximo_numero = vals['proximo_numero']
            seq=None
            if self.tipo_documento=='nota_remision':
                seq = self.journal_id.remision_sequence_id
                s = {
                    'use_date_range': False,
                    'prefix': var_nro_establecimiento + '-' + var_nro_punto_expedicion + '-',
                    'number_increment': 1,
                    'padding': 7,
                    'number_next_actual': var_proximo_numero
                }
                
                seq.write(s)
        else:
            raise exceptions.ValidationError('Debe tener un Diario asignado')
