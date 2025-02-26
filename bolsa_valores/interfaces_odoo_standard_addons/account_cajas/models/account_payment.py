from odoo import api, fields, models, exceptions


class account_payment(models.Model):
    _inherit = 'account.payment'

    caja_session_id = fields.Many2one(
        'account.caja.session', string="Sesión de caja",copy=False)

    def get_sesion(self):
        sesion = self.env['account.caja.session'].search(
                [('company_id', '=', self.company_id.id or self.env.company.id), ('user_id', '=', self.env.user.id), ('state', '=', 'proceso')])
        return sesion
    
    def action_post(self):
        for i in self:
            if i.payment_type == 'inbound' and not i.is_internal_transfer:
                caja = i.get_sesion().caja_id
                if i.journal_id.id not in caja.journal_ids.ids:
                    raise exceptions.ValidationError(
                        'No se puede crear una linea de pago en el diario %s, el mismo no está habilitado para ésta caja.' % i.journal_id.name)
        super(account_payment, self).action_post()
        for r in self:
            if r.state == 'posted' and r.payment_type=='inbound' and not r.is_internal_transfer:
                sesion = r.get_sesion()
                for s in sesion.statement_ids.filtered(lambda x: x.journal_id == r.journal_id):
                    monto = r.amount
                    if r.payment_type == 'outbound':
                        monto = monto*-1
                    value={
                        'date': fields.Date.today(), 
                        'partner_id':r.partner_id.id, 
                        'amount':monto, 
                        'payment_id':r.id, 
                        'journal_id':r.journal_id.id,
                        'statement_id':s.id,
                        'payment_ref':r.name
                    }
                    line_ids = self.env['account.bank.statement.line'].create(value)
                    s.write({'line_ids':[(4,line_ids.id,0)]})

    @api.model
    def create(self, vals):
        if vals.get('payment_type') == 'inbound' and not vals.get('is_internal_transfer'):
            session = self.get_sesion()
            if session:
                vals['caja_session_id'] = session.id
            else:
                raise exceptions.ValidationError(
                    'No existe ninguna sesión de caja abierta para el usuario %s. Antes debe abrir una.' % (self.env.user.name))
        return super(account_payment, self).create(vals)


    def action_cancel(self):
        for i in self:
            if i.payment_type =='inbound' and not i.is_internal_transfer:
                if i.caja_session_id and i.caja_session_id.state in ['cierre','proceso']:
                    res=super(account_payment, i).action_cancel()
                    for st in i.caja_session_id.statement_ids:
                        lines = st.line_ids.filtered(
                            lambda l: l.payment_id == i)
                        if lines:
                            lines.unlink()
                            if i.caja_session_id.state == 'cierre' and st.journal_id.type == 'bank':
                                st.write(
                                    {'balance_end_real': st.balance_end_real-i.amount})
                    return res
                else:
                    raise exceptions.ValidationError(
                        'Sólo se puede cancelar un recibo si su sesión de caja está abierta o en proceso de cierre.')
            else:
                return super(account_payment, i).action_cancel()
            
