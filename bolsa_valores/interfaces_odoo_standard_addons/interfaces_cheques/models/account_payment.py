from odoo import models,fields,api,exceptions


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    tipo_cheque=fields.Selection(string="Tipo de cheque",selection=[('propio','Propio'),('tercero','Tercero')])
    estado_cheque=fields.Selection(string="Estado del cheque",selection=[('pendiente','Pendiente'),('pagado','Pagado'),('rechazado','Rechazado')],copy=False)
    rechazo_move_id=fields.Many2one('account.move',string='Asiento de rechazo',copy=False)


    def marcar_pagado(self):
        self.write({'estado_cheque':'pagado'})


    def write(self,vals):
        for i in self:
            diario_tesoreria=vals.get('journal_actual_id')
            journal_id=self.env['account.journal'].browse(diario_tesoreria)
            if journal_id and not journal_id.es_diario_tesoreria:
                vals['estado_cheque']='pagado'
            return super(AccountPayment,i).write(vals)
            
    @api.model
    def create(self,vals):
        payment_type=vals.get('payment_type')
        tipo_pago=vals.get('tipo_pago')
        if tipo_pago=='Cheque':
            if payment_type=='inbound':
                vals['tipo_cheque']='tercero'
            elif payment_type=='inbound':
                vals['tipo_cheque']='propio'
            vals['estado_cheque']='pendiente'
        return super(AccountPayment,self).create(vals)